#!/usr/bin/env python3
"""Rebuild/validate the pre-specified exact-mode different-surface Tanakh sensitivity.

Runs from the repository root regardless of the current working directory.
--verify compares recorded results to the pinned cross-corpus references.
--recompute reconstructs word-host motifs from pinned Tanakh source JSON and
writes new results only to .local (never changes the frozen reference CSVs).
"""
from __future__ import annotations
import argparse,collections,csv,hashlib,json,statistics,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src'),str(ROOT/'src/analysis')]
from src.analysis.poetic_comparators import compute_spatial_for,compute_different_surface_coverage
from src.tanakh import primary, prepare

OUT=ROOT/'results/tanakh/word_control'
EXACT_ABS_TOL=3e-11

def read(path):
    with path.open(encoding='utf-8',newline='') as file:
        return list(csv.DictReader(file))

def write(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=list(rows[0]),lineterminator='\n')
        writer.writeheader();writer.writerows(rows)

def key(row):
    name=row['corpus'].replace('Song of Songs','Song_of_Songs')
    return name,row['condition'],str(row['radius']),row['control']

def same(a,b,which):
    if abs(float(a)-float(b))>EXACT_ABS_TOL:
        raise ValueError(f"{which}: {a!r} != {b!r}")

def validate(spatial,replicates,coverage):
    if len(spatial)!=702 or len(replicates)!=13338 or len(coverage)!=39:
        raise ValueError('Unexpected result shape: expected 702/13338/39 rows')
    by_book={r['source_book']:r for r in read(ROOT/'results/tanakh/primary/source_books_39.csv')}
    if len(by_book)!=39 or set(r['corpus'] for r in spatial)!=set(by_book):
        raise ValueError('Tanakh book inventory mismatch')
    comparison_reference={key(r):r for r in read(ROOT/'results/controls/different_surface_spatial.csv')}
    rep_map=collections.defaultdict(list)
    for r in replicates:
        if int(r['replicate']) not in range(19):raise ValueError('Invalid replicate index')
        rep_map[key(r)].append(float(r['coverage']))
    overlap=primary_check=0
    for row in spatial:
        k=key(row); samples=rep_map[k]
        if len(samples)!=19:raise ValueError(f'Expected 19 replicates for {k}, got {len(samples)}')
        for field,actual in (('null_mean',statistics.mean(samples)),('null_min',min(samples)),('null_max',max(samples))):
            same(row[field],actual,(k,field))
        same(float(row['observed'])-float(row['null_mean']),row['delta'],(k,'delta'))
        if k in comparison_reference:
            for field in ('blocks','retained_fraction','observed','null_mean','delta','null_min','null_max'):
                same(row[field],comparison_reference[k][field],(k,field))
            overlap+=1
        if row['condition']=='baseline_exact' and str(row['radius'])=='64':
            col={'local128':'spatial_local_exact','regional1024':'spatial_regional_exact','whole_corpus':'spatial_whole_exact'}[row['control']]
            same(row['delta'],by_book[row['corpus']][col],(k,col));primary_check+=1
    if overlap!=180 or primary_check!=117:raise ValueError(f'Cross checks incomplete: {overlap}/180, {primary_check}/117')
    if len({(key(r),r['replicate']) for r in replicates})!=13338:
        raise ValueError('Duplicate replicate keys')
    if len({r['book'] for r in coverage})!=39:raise ValueError('Coverage book inventory mismatch')
    for row in coverage:
        name=row['book']
        same(row['baseline_coverage_R64'],by_book[name]['coverage_exact'],(name,'primary coverage'))
        same(float(row['baseline_coverage_R64'])-float(row['different_surface_coverage_R64']),row['absolute_reduction'],(name,'reduction'))
        if not (0 < float(row['different_surface_coverage_R64']) < float(row['baseline_coverage_R64'])):
            raise ValueError(f'{name}: inconsistent different-surface coverage')
    print('PASS word-control: 39 books; 702 spatial rows; 13,338 replicates')
    print('PASS 180 comparator-overlap and 117 primary regressions; 39 coverage rows')

def make_coverage_row(name,traditional_name,word_count,results):
    idx={(r['condition'],int(r['block']),int(r['offset']),int(r['radius'])):r for r in results}
    a=idx['baseline_exact',512,0,64];b=idx['different_surface_word',512,0,64]
    ab=float(a['mean']);bb=float(b['mean'])
    return dict(book=name,traditional_book=traditional_name,words=word_count,blocks_512=a['blocks'],
                baseline_coverage_R64=ab,different_surface_coverage_R64=bb,
                absolute_reduction=ab-bb,retained_fraction_of_baseline=bb/ab if ab else '')

# Inputs used directly or indirectly by the pinned word-control calculation.
# Include the active code as well as frozen metadata: an uncommitted code edit must
# invalidate a checkpoint even if config/manifest.json has not been regenerated.
FINGERPRINT_INPUTS=(
    'run/tanakh_word_control.py',
    'src/analysis/poetic_comparators.py',
    'src/analysis/compare_modes.py',
    'src/analysis/spatial.py',
    'src/tanakh/primary.py',
    'src/tanakh/prepare.py',
    'src/core/phonetic_core_v2.py',
    'src/preparation/prepare_biblical_reading.py',
    'src/prepare.py',
    'src/core/perpetual_qere.py',
    'config/tanakh/source_freeze.json',
    'config/tanakh/editorial_repeat_tails.json',
    'config/tanakh/ketiv_without_qere.json',
    'config/manifest.json',
)

def fingerprint(row):
    source=ROOT/'sources/original/tanakh'/f"{int(row['order']):02d}_{prepare.safe_slug(row['source_book'])}.json"
    files=[source]+[ROOT/rel for rel in FINGERPRINT_INPUTS]
    digest=hashlib.sha256()
    for path in files:
        # Bind path names as well as bytes to prevent accidental aliasing.
        digest.update(str(path.relative_to(ROOT)).replace('\\','/').encode('utf-8'))
        digest.update(b'\0')
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()

def recompute(only_book=None):
    frozen=prepare.load_json('config/tanakh/source_freeze.json')['source_books']
    raw=ROOT/'sources/original/tanakh'
    config={'editorial':{r['ref']:r for r in prepare.load_json('config/tanakh/editorial_repeat_tails.json')['rules']},
            'kwq':{r['ref']:r for r in prepare.load_json('config/tanakh/ketiv_without_qere.json')['rules']}}
    spatial=[];replicates=[];coverage=[]
    checkpoints=ROOT/'.local/word_control_checkpoints'
    checkpoints.mkdir(parents=True,exist_ok=True)
    for n,row in enumerate(frozen,1):
        name=row['source_book']
        if only_book and name!=only_book:continue
        print(f'[{n:02d}/39] {name}',flush=True)
        cp=checkpoints/(f"{int(row['order']):02d}_{prepare.safe_slug(name)}.json")
        sig=fingerprint(row)
        cached=json.loads(cp.read_text(encoding='utf-8')) if cp.exists() else {}
        if cached.get('signature')==sig:
            print('  verified cached computation',flush=True)
            a,b,covrow=cached['spatial'],cached['replicates'],cached['coverage']
        else:
            sounds,wordpairs,invalid_positions=primary.prepare_stream(row,raw,config)
            # `invalid_positions` flags cross-psalm triplet starts, not unresolved tokens.
            if name != 'Psalms' and invalid_positions:
                raise ValueError(f'{name}: unexpected forbidden motif starts')
            words=[tuple(p[0]) for p in wordpairs]
            hard=set()
            if name=='Psalms':
                hard={i for i in range(1,len(wordpairs)) if wordpairs[i][1]!=wordpairs[i-1][1]}
            a,b=compute_spatial_for(name,[words],[hard],modes=(('baseline_exact',False,False),('different_surface_word',True,False)))
            cov=compute_different_surface_coverage({name:([words],[hard])})
            covrow=make_coverage_row(name,row['traditional_24_book'],len(words),cov)
            temp=cp.with_suffix('.tmp')
            temp.write_text(json.dumps({'signature':sig,'spatial':a,'replicates':b,'coverage':covrow})+'\n',encoding='utf-8')
            temp.replace(cp)
        coverage.append(covrow)
        spatial.extend(a);replicates.extend(b)
    if not only_book:validate(spatial,replicates,coverage)
    dest=ROOT/'.local/word_control_recomputed'
    write(dest/'different_surface_spatial.csv',spatial)
    write(dest/'different_surface_spatial_replicates.csv',replicates)
    write(dest/'different_surface_coverage_summary.csv',coverage)
    reference=[('different_surface_spatial.csv',spatial),('different_surface_spatial_replicates.csv',replicates),('different_surface_coverage_summary.csv',coverage)]
    for name,rows in reference:
        expected=read(OUT/name)
        if only_book:expected=[r for r in expected if r.get('corpus',r.get('book'))==only_book]
        if len(rows)!=len(expected):raise ValueError(f'{name} row count differs')
        for row1,row2 in zip(rows,expected):
            if set(row1)!=set(row2):raise ValueError(f'{name} columns differ')
            for col in row1:
                try:
                    float(row1[col]);float(row2[col])
                except (TypeError,ValueError):
                    if str(row1[col])!=str(row2[col]):raise ValueError(f'{name}: {col} mismatch: {row1[col]} != {row2[col]}')
                else:same(row1[col],row2[col],(name,row1.get('corpus',row1.get('book')),col))
    print('PASS independently recomputed output matches frozen word-control tables')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    group=ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--verify',action='store_true')
    group.add_argument('--recompute',action='store_true')
    ap.add_argument('--book',help='Recompute and check a single source book (smoke test)')
    opts=ap.parse_args()
    if opts.verify:validate(read(OUT/'different_surface_spatial.csv'),read(OUT/'different_surface_spatial_replicates.csv'),read(OUT/'different_surface_coverage_summary.csv'))
    else:recompute(opts.book)
if __name__=='__main__':main()
