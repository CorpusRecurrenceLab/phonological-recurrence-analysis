#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, random, statistics, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
sys.path.insert(0, str(SRC))
import primary as s3  # noqa: E402

AFFECTED = ('Genesis', 'Jeremiah', 'Daniel', 'Ezra')
MODES = ('exact', 'expanded')
CONTROLS = ('local128', 'regional1024', 'whole_corpus')


def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def close(a, b, tol=2e-11):
    if a is None or b is None:
        return a is None and b is None
    return abs(float(a) - float(b)) <= tol


def prepare_language_runs(book_row: dict, raw_dir: Path, configs: dict):
    book = book_row['source_book']
    path = raw_dir / f"{int(book_row['order']):02d}_{s3.s2.safe_slug(book)}.json"
    if not path.is_file():
        raise FileNotFoundError(f'Missing frozen source cache: {path}')
    data = path.read_bytes()
    got = s3.s2.git_blob_sha1(data)
    if got != book_row['git_blob_sha1']:
        raise ValueError(f'Git blob mismatch for {book}: expected {book_row["git_blob_sha1"]}, got {got}')
    obj = json.loads(data.decode('utf-8'))

    language_runs = {'hebrew': [], 'aramaic': []}
    active_language = None
    active_run = None
    totals = {'words': 0, 'sound_units': 0, 'aramaic_words': 0, 'aramaic_sound_units': 0}

    for ci, chapter in enumerate(obj['text'], 1):
        for vi, source in enumerate(chapter, 1):
            ref = f'{book} {ci}:{vi}'
            source, _ = s3.s2.strip_editorial_tail(source, ref, configs['editorial'])
            reading, _edits, _ = s3.adapt(source)
            reading, _ = s3.s2.omit_ketiv_without_qere(reading, ref, configs['kwq'])
            token_index = 0
            for match in s3.s2.TOKEN.finditer(reading):
                token_index += 1
                units = s3.transliterate_word(match.group(), return_units=True)
                if not units:
                    raise ValueError(f'Unresolved Aramaic-sensitivity token at {ref}#{token_index}: {match.group()}')
                is_ar = s3.s2.is_aramaic_token(book, ci, vi, token_index)
                language = 'aramaic' if is_ar else 'hebrew'
                if language != active_language:
                    active_run = {'sounds': [], 'words': []}
                    language_runs[language].append(active_run)
                    active_language = language
                active_run['sounds'].extend(units)
                active_run['words'].append((units, ci))
                totals['words'] += 1
                totals['sound_units'] += len(units)
                if is_ar:
                    totals['aramaic_words'] += 1
                    totals['aramaic_sound_units'] += len(units)

    return language_runs, totals


def coverage_grid_runs(runs):
    total = sum(len(run['sounds']) for run in runs)
    out = []
    for L in (512, 1280):
        for offset in (0, L // 2):
            vals = {(m, r): [] for m in MODES for r in s3.RADII}
            for run in runs:
                sounds = run['sounds']
                for start in range(offset, len(sounds) - L + 1, L):
                    counts = s3.coverage_counts(L, s3.occurrences(sounds[start:start + L]))
                    for mi, mode in enumerate(MODES):
                        for ri, radius in enumerate(s3.RADII):
                            vals[mode, radius].append(counts[mi][ri] / L)
            for mode in MODES:
                for radius in s3.RADII:
                    v = vals[mode, radius]
                    out.append({
                        'mode': mode, 'block': L, 'offset': offset, 'radius': radius,
                        'blocks': len(v),
                        'retained_fraction': (len(v) * L / total) if v and total else None,
                        'mean': statistics.mean(v) if v else None,
                    })
    return out


def distance_grid_runs(runs):
    total = sum(len(run['sounds']) for run in runs)
    out = []
    for cap, L in ((256, 512), (1024, 1280), (4096, 4352)):
        gaps = [g for g in (0, 64, 256, 1024, 4096) if g <= cap]
        for offset in (0, L // 2):
            for phase in (0, 64):
                block_values = {(m, g): [] for m in MODES for g in gaps}
                anchors = 0
                for run in runs:
                    sounds = run['sounds']
                    for start in range(offset, len(sounds) - L + 1, L):
                        cache = {}
                        def motifs(i):
                            if i not in cache:
                                cache[i] = {t for t, _ in s3.occurrences(sounds[i:i + 64])}
                            return cache[i]
                        vals = {(m, g): [] for m in MODES for g in gaps}
                        for i in range(start + phase, start + L - 128 - cap + 1, 128):
                            anchors += 1
                            for gap in gaps:
                                sim = s3.similarity(motifs(i), motifs(i + 64 + gap))
                                for mi, mode in enumerate(MODES):
                                    vals[mode, gap].append(sim[mi])
                        for key, v in vals.items():
                            if v:
                                block_values[key].append(statistics.mean(v))
                for mode in MODES:
                    for gap in gaps:
                        v = block_values[mode, gap]
                        out.append({
                            'mode': mode, 'cap': cap, 'block': L, 'offset': offset,
                            'phase': phase, 'gap': gap, 'blocks': len(v), 'anchors': anchors,
                            'retained_fraction': (len(v) * L / total) if v and total else None,
                            'mean': statistics.mean(v) if v else None,
                        })
    return out


def _fragment(words):
    seq = []
    for units, _chapter in words:
        seq.extend(units)
    return len(seq), s3.occurrences(seq)


def spatial_grid_runs(runs):
    total = sum(len(run['sounds']) for run in runs)
    run_frags = []
    retained = 0
    blocks = 0
    for run in runs:
        words = run['words']
        n = len(words) // 128 * 128
        frags = [_fragment(words[i:i + 8]) for i in range(0, n, 8)]
        if frags:
            run_frags.append(frags)
            blocks += len(frags) // 16
            retained += sum(length for length, _items in frags)

    def evaluate(orders):
        if not retained:
            return [[None] * 3 for _ in range(2)]
        sums = [[0] * 3 for _ in range(2)]
        for frags, order in zip(run_frags, orders):
            for k in range(0, len(order), 16):
                pos = 0
                items = []
                for idx in order[k:k + 16]:
                    length, its = frags[idx]
                    items.extend((t, pos + i) for t, i in its)
                    pos += length
                v = s3.coverage_counts(pos, items)
                for mi in range(2):
                    for ri in range(3):
                        sums[mi][ri] += v[mi][ri]
        return [[x / retained for x in row] for row in sums]

    base_orders = [list(range(len(frags))) for frags in run_frags]
    observed = evaluate(base_orders)
    out = []
    for control in CONTROLS:
        permutations = []
        for rep in range(19):
            rng = random.Random(2026102601 + rep)
            orders = []
            for frags in run_frags:
                order = list(range(len(frags)))
                if control == 'local128':
                    ranges = [(i, i + 16) for i in range(0, len(order), 16)]
                elif control == 'regional1024':
                    ranges = [(i, min(i + 128, len(order))) for i in range(0, len(order), 128)]
                else:
                    ranges = [(0, len(order))]
                for a, b in ranges:
                    sub = order[a:b]
                    rng.shuffle(sub)
                    order[a:b] = sub
                orders.append(order)
            permutations.append(evaluate(orders))

        for mi, mode in enumerate(MODES):
            for ri, radius in enumerate(s3.RADII):
                if not retained:
                    out.append({
                        'mode': mode, 'radius': radius, 'control': control,
                        'blocks': 0, 'retained_units': 0, 'total_units': total,
                        'retained_fraction': None, 'observed': None, 'null_mean': None,
                        'delta': None, 'null_min': None, 'null_max': None,
                    })
                    continue
                vals = [v[mi][ri] for v in permutations]
                mu = statistics.mean(vals)
                out.append({
                    'mode': mode, 'radius': radius, 'control': control,
                    'blocks': blocks, 'retained_units': retained, 'total_units': total,
                    'retained_fraction': retained / total if total else None,
                    'observed': observed[mi][ri], 'null_mean': mu,
                    'delta': observed[mi][ri] - mu,
                    'null_min': min(vals), 'null_max': max(vals),
                })
    return out


def primary_from_grids(cov, dist, spatial):
    coverage = {}
    for mode in MODES:
        row = next(r for r in cov if r['mode'] == mode and r['block'] == 512 and r['offset'] == 0 and r['radius'] == 64)
        coverage[mode] = row['mean']
    distance = {}
    for mode in MODES:
        contrasts = []
        complete = True
        for offset in (0, 640):
            for phase in (0, 64):
                r0 = next(r for r in dist if r['mode'] == mode and r['cap'] == 1024 and r['offset'] == offset and r['phase'] == phase and r['gap'] == 0)
                r1 = next(r for r in dist if r['mode'] == mode and r['cap'] == 1024 and r['offset'] == offset and r['phase'] == phase and r['gap'] == 1024)
                if r0['mean'] is None or r1['mean'] is None:
                    complete = False
                    break
                contrasts.append(r0['mean'] - r1['mean'])
            if not complete:
                break
        distance[mode] = statistics.mean(contrasts) if complete and len(contrasts) == 4 else None
    spatial_primary = {}
    for control in CONTROLS:
        spatial_primary[control] = {}
        for mode in MODES:
            row = next(r for r in spatial if r['control'] == control and r['radius'] == 64 and r['mode'] == mode)
            spatial_primary[control][mode] = row['delta']
    return {'coverage': coverage, 'distance': distance, 'spatial': spatial_primary}


def _fmt(value):
    if value is None:
        return 'NA'
    if isinstance(value, int):
        return str(value)
    x = float(value)
    if x.is_integer():
        return str(int(x))
    return f'{x:.12f}'


def fnv1a64_ascii(text: str):
    h = 0xCBF29CE484222325
    for byte in text.encode('ascii'):
        h ^= byte
        h = (h * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return f'{h:016x}'


def grid_fingerprint(cov, dist, spatial):
    parts = []
    for block in (512, 1280):
        for offset in (0, block // 2):
            subset = [r for r in cov if r['block'] == block and r['offset'] == offset]
            blocks = subset[0]['blocks']
            retained = subset[0]['retained_fraction']
            values = []
            for mode in MODES:
                for radius in s3.RADII:
                    values.append(next(r['mean'] for r in subset if r['mode'] == mode and r['radius'] == radius))
            parts.append('C|' + '|'.join(_fmt(x) for x in (block, offset, blocks, retained, *values)))
    for cap, block in ((256, 512), (1024, 1280), (4096, 4352)):
        gaps = [g for g in (0, 64, 256, 1024, 4096) if g <= cap]
        for offset in (0, block // 2):
            for phase in (0, 64):
                subset = [r for r in dist if r['cap'] == cap and r['offset'] == offset and r['phase'] == phase]
                first = subset[0]
                exact = [next(r['mean'] for r in subset if r['mode'] == 'exact' and r['gap'] == g) for g in gaps]
                expanded = [next(r['mean'] for r in subset if r['mode'] == 'expanded' and r['gap'] == g) for g in gaps]
                prefix = [cap, offset, phase, first['blocks'], first['anchors'], first['retained_fraction']]
                parts.append('D|' + '|'.join([
                    *(_fmt(x) for x in prefix),
                    ':'.join(str(g) for g in gaps),
                    ':'.join(_fmt(x) for x in exact),
                    ':'.join(_fmt(x) for x in expanded),
                ]))
    for control in CONTROLS:
        subset = [r for r in spatial if r['control'] == control]
        first = subset[0]
        vals = []
        for mode in MODES:
            for radius in s3.RADII:
                r = next(x for x in subset if x['mode'] == mode and x['radius'] == radius)
                vals.extend((r['observed'], r['null_mean'], r['delta'], r['null_min'], r['null_max']))
        parts.append('S|' + '|'.join([control, *(_fmt(x) for x in (first['blocks'], first['retained_units'], first['total_units'], *vals))]))
    return fnv1a64_ascii('\n'.join(parts))


def validate_result(book, label, result, expected):
    for key in ('words', 'sounds', 'runs'):
        if result[key] != expected[key]:
            raise AssertionError(f'{book}/{label} {key}: expected {expected[key]}, got {result[key]}')
    for metric in ('coverage', 'distance'):
        for mode in MODES:
            if not close(result['primary'][metric][mode], expected['primary'][metric][mode]):
                raise AssertionError(f'{book}/{label} {metric}/{mode}: expected {expected["primary"][metric][mode]!r}, got {result["primary"][metric][mode]!r}')
    for control in CONTROLS:
        for mode in MODES:
            if not close(result['primary']['spatial'][control][mode], expected['primary']['spatial'][control][mode]):
                raise AssertionError(f'{book}/{label} spatial {control}/{mode}: mismatch')
    if result['full_grid_fnv1a64'] != expected['hash']:
        raise AssertionError(f'{book}/{label} full-grid fingerprint: expected {expected["hash"]}, got {result["full_grid_fnv1a64"]}')


def analyze_runs(runs):
    cov = coverage_grid_runs(runs)
    dist = distance_grid_runs(runs)
    spatial = spatial_grid_runs(runs)
    return {
        'words': sum(len(r['words']) for r in runs),
        'sounds': sum(len(r['sounds']) for r in runs),
        'runs': len(runs),
        'primary': primary_from_grids(cov, dist, spatial),
        'coverage_grid': cov,
        'distance_grid': dist,
        'spatial_grid': spatial,
        'full_grid_fnv1a64': grid_fingerprint(cov, dist, spatial),
    }


def source_39_table(stage3_expected, computed):
    out = []
    for frozen in stage3_expected['source_books']:
        book = frozen['source_book']
        if book in computed:
            x = computed[book]['exclusion']
            primary = x['primary']; words = x['words']; sounds = x['sounds']; status = 'recalculated_hard_gap'
        else:
            primary = frozen['primary']; words = frozen['word_count']; sounds = frozen['sound_unit_count']; status = 'unchanged_no_declared_aramaic_mask'
        out.append({
            'order': frozen['order'], 'source_book': book, 'traditional_24_book': frozen['traditional_24_book'],
            'git_blob_sha1': frozen['git_blob_sha1'], 'word_count': words, 'sound_unit_count': sounds,
            'status': status, 'primary': primary,
        })
    return out


def aggregate_ezra_nehemiah(computed_ezra, stage3_expected):
    ez = computed_ezra
    ne_frozen = next(x for x in stage3_expected['source_books'] if x['source_book'] == 'Nehemiah')
    ne = ne_frozen['primary']
    detail = stage3_expected['multi_source_reporting_detail']['Nehemiah']

    cov = {}
    ez_cov_blocks = next(r['blocks'] for r in ez['coverage_grid'] if r['mode'] == 'exact' and r['block'] == 512 and r['offset'] == 0 and r['radius'] == 64)
    for mode in MODES:
        cov[mode] = (ez['primary']['coverage'][mode] * ez_cov_blocks + ne['coverage'][mode] * detail['cblocks']) / (ez_cov_blocks + detail['cblocks'])

    dist = {}
    for mode_index, mode in enumerate(MODES):
        conditions = []
        for ci, (offset, phase) in enumerate(((0, 0), (0, 64), (640, 0), (640, 64))):
            e0 = next(r for r in ez['distance_grid'] if r['mode'] == mode and r['cap'] == 1024 and r['offset'] == offset and r['phase'] == phase and r['gap'] == 0)
            e1 = next(r for r in ez['distance_grid'] if r['mode'] == mode and r['cap'] == 1024 and r['offset'] == offset and r['phase'] == phase and r['gap'] == 1024)
            ez_delta = e0['mean'] - e1['mean']
            ez_blocks = e0['blocks']
            ne_delta = detail['d4'][mode_index][ci]
            ne_blocks = detail['db'][0 if ci < 2 else 1]
            conditions.append((ez_delta * ez_blocks + ne_delta * ne_blocks) / (ez_blocks + ne_blocks))
        dist[mode] = statistics.mean(conditions)

    spatial = {}
    ez_retained = next(r['retained_units'] for r in ez['spatial_grid'] if r['control'] == 'local128' and r['mode'] == 'exact' and r['radius'] == 64)
    for control in CONTROLS:
        spatial[control] = {}
        for mode in MODES:
            spatial[control][mode] = (
                ez['primary']['spatial'][control][mode] * ez_retained +
                ne['spatial'][control][mode] * detail['ret']
            ) / (ez_retained + detail['ret'])

    return {
        'traditional_book': 'Ezra-Nehemiah', 'source_books': 2, 'components': ['Ezra', 'Nehemiah'],
        'words': ez['words'] + ne_frozen['word_count'], 'sound_units': ez['sounds'] + ne_frozen['sound_unit_count'],
        'coverage_exact': cov['exact'], 'coverage_expanded': cov['expanded'],
        'distance_exact': dist['exact'], 'distance_expanded': dist['expanded'],
        'spatial_local_exact': spatial['local128']['exact'], 'spatial_local_expanded': spatial['local128']['expanded'],
        'spatial_regional_exact': spatial['regional1024']['exact'], 'spatial_regional_expanded': spatial['regional1024']['expanded'],
        'spatial_whole_exact': spatial['whole_corpus']['exact'], 'spatial_whole_expanded': spatial['whole_corpus']['expanded'],
        'reporting_aggregation': 'pooled eligible source-book blocks/material; no cross-source motifs',
    }


def reporting_24(stage3_expected, computed):
    out = []
    for frozen in stage3_expected['reporting_24']:
        name = frozen['traditional_book']
        if name in ('Genesis', 'Jeremiah', 'Daniel'):
            x = computed[name]['exclusion']; p = x['primary']
            row = dict(frozen)
            row.update({
                'words': x['words'], 'sound_units': x['sounds'],
                'coverage_exact': p['coverage']['exact'], 'coverage_expanded': p['coverage']['expanded'],
                'distance_exact': p['distance']['exact'], 'distance_expanded': p['distance']['expanded'],
                'spatial_local_exact': p['spatial']['local128']['exact'], 'spatial_local_expanded': p['spatial']['local128']['expanded'],
                'spatial_regional_exact': p['spatial']['regional1024']['exact'], 'spatial_regional_expanded': p['spatial']['regional1024']['expanded'],
                'spatial_whole_exact': p['spatial']['whole_corpus']['exact'], 'spatial_whole_expanded': p['spatial']['whole_corpus']['expanded'],
            })
        elif name == 'Ezra-Nehemiah':
            row = aggregate_ezra_nehemiah(computed['Ezra']['exclusion'], stage3_expected)
        else:
            row = dict(frozen)
        out.append(row)
    return out


def validate_reporting(observed, expected):
    if len(observed) != len(expected):
        raise AssertionError('24-book reporting row-count mismatch')
    for a, b in zip(observed, expected):
        if a['traditional_book'] != b['traditional_book']:
            raise AssertionError('24-book reporting order/name mismatch')
        for key, exp in b.items():
            got = a[key]
            if isinstance(exp, (int, str, list)) or exp is None:
                if got != exp:
                    raise AssertionError(f'{a["traditional_book"]} {key}: expected {exp!r}, got {got!r}')
            else:
                if not close(got, exp):
                    raise AssertionError(f'{a["traditional_book"]} {key}: expected {exp!r}, got {got!r}')


def write_source_csv(path, rows):
    fields = ['source_book', 'git_blob_sha1', 'status', 'words', 'sound_units', 'coverage_exact', 'coverage_expanded',
              'distance_exact', 'distance_expanded', 'spatial_local_exact', 'spatial_local_expanded',
              'spatial_regional_exact', 'spatial_regional_expanded', 'spatial_whole_exact', 'spatial_whole_expanded']
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator='\n'); w.writeheader()
        for x in rows:
            p = x['primary']
            w.writerow({
                'source_book': x['source_book'], 'git_blob_sha1': x['git_blob_sha1'], 'status': x['status'],
                'words': x['word_count'], 'sound_units': x['sound_unit_count'],
                'coverage_exact': p['coverage']['exact'], 'coverage_expanded': p['coverage']['expanded'],
                'distance_exact': p['distance']['exact'], 'distance_expanded': p['distance']['expanded'],
                'spatial_local_exact': p['spatial']['local128']['exact'], 'spatial_local_expanded': p['spatial']['local128']['expanded'],
                'spatial_regional_exact': p['spatial']['regional1024']['exact'], 'spatial_regional_expanded': p['spatial']['regional1024']['expanded'],
                'spatial_whole_exact': p['spatial']['whole_corpus']['exact'], 'spatial_whole_expanded': p['spatial']['whole_corpus']['expanded'],
            })


def write_24_csv(path, rows):
    fields = ['traditional_book', 'source_books', 'components', 'words', 'sound_units', 'coverage_exact', 'coverage_expanded',
              'distance_exact', 'distance_expanded', 'spatial_local_exact', 'spatial_local_expanded',
              'spatial_regional_exact', 'spatial_regional_expanded', 'spatial_whole_exact', 'spatial_whole_expanded', 'reporting_aggregation']
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator='\n'); w.writeheader()
        for row in rows:
            z = dict(row); z['components'] = ' + '.join(z['components']); w.writerow(z)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-work', default=str(ROOT / 'work' / 'preparation'))
    ap.add_argument('--output-dir', default=str(ROOT / 'work' / 'sensitivity'))
    args = ap.parse_args()
    raw_dir = Path(args.source_work).resolve() / 'sources_raw'
    outdir = Path(args.output_dir).resolve(); outdir.mkdir(parents=True, exist_ok=True)

    expected = load_json(ROOT / 'config' / 'aramaic_sensitivity_expected.json')
    stage3_expected = load_json(ROOT / 'config' / 'primary_expected.json')
    freeze = load_json(ROOT / 'config' / 'source_freeze.json')
    kwq = load_json(ROOT / 'config' / 'ketiv_without_qere.json')
    editorial = load_json(ROOT / 'config' / 'editorial_repeat_tails.json')
    configs = {'kwq': {r['ref']: r for r in kwq['rules']}, 'editorial': {r['ref']: r for r in editorial['rules']}}
    rows_by_book = {r['source_book']: r for r in freeze['source_books']}

    computed = {}
    for book in AFFECTED:
        print(f'[Aramaic sensitivity] {book} ...', flush=True)
        runs, totals = prepare_language_runs(rows_by_book[book], raw_dir, configs)
        if totals['words'] != next(x['word_count'] for x in stage3_expected['source_books'] if x['source_book'] == book):
            raise AssertionError(f'{book}: full-stream word count changed from primary')
        exclusion = analyze_runs(runs['hebrew'])
        aramaic = analyze_runs(runs['aramaic'])
        frozen = expected['affected_books'][book]
        validate_result(book, 'exclusion', exclusion, frozen['exclusion'])
        validate_result(book, 'aramaic_only', aramaic, frozen['aramaic_only'])
        computed[book] = {'exclusion': exclusion, 'aramaic_only': aramaic, 'totals': totals}

    source_rows = source_39_table(stage3_expected, computed)
    if sum(r['word_count'] for r in source_rows) != expected['counts']['exclusion_words']:
        raise AssertionError('Aramaic-sensitivity exclusion word total mismatch')
    if sum(r['sound_unit_count'] for r in source_rows) != expected['counts']['exclusion_sound_units']:
        raise AssertionError('Aramaic-sensitivity exclusion sound-unit total mismatch')
    reporting = reporting_24(stage3_expected, computed)
    validate_reporting(reporting, expected['exclusion_reporting_24'])

    full = {'affected_books': computed, 'source_books_exclusion': source_rows, 'traditional_24_exclusion': reporting}
    (outdir / 'stage4_full_results.json').write_text(json.dumps(full, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    write_source_csv(outdir / 'aramaic_exclusion_source_books_39.csv', source_rows)
    write_24_csv(outdir / 'aramaic_exclusion_traditional_24.csv', reporting)

    status = {
        'status': 'PASS', 'affected_source_books': 4, 'source_books_exclusion': 39, 'traditional_books_exclusion': 24,
        'exclusion_words': sum(r['word_count'] for r in source_rows),
        'exclusion_sound_units': sum(r['sound_unit_count'] for r in source_rows),
        'detail': 'Aramaic-sensitivity Aramaic-span exclusion sensitivity and complementary Aramaic-only descriptive check reproduce frozen values with hard language gaps.'
    }
    (outdir / 'status.json').write_text(json.dumps(status, indent=2) + '\n', encoding='utf-8', newline='\n')
    print('PASS Aramaic sensitivity Aramaic-span sensitivity: 4 affected source-books')
    print('PASS exclusion reporting: 39 source-books / 24 traditional books')
    print('PASS complementary Aramaic-only descriptive check (fixed geometries; NA retained where impossible)')


if __name__ == '__main__':
    main()
