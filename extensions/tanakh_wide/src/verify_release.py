#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json, py_compile, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def load(p): return json.loads((ROOT/p).read_text(encoding='utf-8'))
def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def git_blob(p):
    data=p.read_bytes(); return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def close(a,b,t=2e-11):
    if a in ('',None) or b is None: return (a in ('',None)) and b is None
    return abs(float(a)-float(b))<=t

def main():
    manifest=load('CHECKSUMS.json')
    for rel,want in manifest['files'].items():
        p=ROOT/rel
        if not p.is_file(): raise AssertionError(f'missing frozen file: {rel}')
        got=sha256(p)
        if got!=want: raise AssertionError(f'checksum mismatch: {rel}')
    source=load('config/source_freeze.json'); prep=load('config/preparation_expected.json'); primary=load('config/primary_expected.json'); sens=load('config/aramaic_sensitivity_expected.json'); m24=load('config/traditional_24_map.json')
    assert len(source['source_books'])==39 and len(m24['traditional_books'])==24
    assert prep['counts']['source_books']==39 and prep['counts']['traditional_books']==24
    assert prep['counts']['words']==305584 and prep['counts']['sound_units']==1602109
    assert primary['counts']['words']==prep['counts']['words'] and primary['counts']['sound_units']==prep['counts']['sound_units']
    assert sens['counts']['primary_words']==prep['counts']['words'] and sens['counts']['primary_sound_units']==prep['counts']['sound_units']
    assert sens['counts']['masked_aramaic_words']==4829 and sens['counts']['masked_aramaic_sound_units']==25727
    assert sens['counts']['exclusion_words']==300755 and sens['counts']['exclusion_sound_units']==1576382
    assert source['source']['mirror_commit']==prep['source_mirror_commit']==primary['source_mirror_commit']==sens['source_mirror_commit']
    assert prep['base_project_commit']==primary['base_project_commit']==sens['base_project_commit']=='a58c44c650bea66f73398ae05c2542b74835566e'
    # Cross-file source identity.
    sb={x['source_book']:x for x in source['source_books']}; pb={x['source_book']:x for x in prep['source_books']}; pr={x['source_book']:x for x in primary['source_books']}
    assert set(sb)==set(pb)==set(pr) and len(sb)==39
    for b in sb:
        assert sb[b]['git_blob_sha1']==pb[b]['git_blob_sha1']==pr[b]['git_blob_sha1']
        assert pb[b]['word_count']==pr[b]['word_count'] and pb[b]['sound_unit_count']==pr[b]['sound_unit_count']
    # Core files remain byte-identical to the frozen base blobs.
    core=load('config/base_code_freeze.json')
    for item in core['files']:
        p=ROOT/item['package_path']
        assert git_blob(p)==item['git_blob_sha1'], f'base-code blob mismatch: {p.name}'
    # Result CSVs reproduce frozen primary tables.
    with (ROOT/'results/primary/source_books_39.csv').open(encoding='utf-8',newline='') as f: rows=list(csv.DictReader(f))
    assert len(rows)==39
    for row in rows:
        x=pr[row['source_book']]['primary']
        expected={'coverage_exact':x['coverage']['exact'],'coverage_expanded':x['coverage']['expanded'],'distance_exact':x['distance']['exact'],'distance_expanded':x['distance']['expanded'],'spatial_local_exact':x['spatial']['local128']['exact'],'spatial_local_expanded':x['spatial']['local128']['expanded'],'spatial_regional_exact':x['spatial']['regional1024']['exact'],'spatial_regional_expanded':x['spatial']['regional1024']['expanded'],'spatial_whole_exact':x['spatial']['whole_corpus']['exact'],'spatial_whole_expanded':x['spatial']['whole_corpus']['expanded']}
        for k,v in expected.items(): assert close(row[k],v), f'primary CSV mismatch {row["source_book"]}/{k}'
    # Sensitivity tables reproduce the frozen language-layer expectations.
    with (ROOT/'results/sensitivity/exclusion_source_books_39.csv').open(encoding='utf-8',newline='') as f: exrows=list(csv.DictReader(f))
    exexp={x['source_book']:x for x in sens['exclusion_source_books']}
    assert len(exrows)==39 and set(r['source_book'] for r in exrows)==set(exexp)
    for row in exrows:
        x=exexp[row['source_book']]; p=x['primary']
        assert row['git_blob_sha1']==x['git_blob_sha1'] and int(row['words'])==x['word_count'] and int(row['sound_units'])==x['sound_unit_count'] and row['status']==x['status']
        vals={'coverage_exact':p['coverage']['exact'],'coverage_expanded':p['coverage']['expanded'],'distance_exact':p['distance']['exact'],'distance_expanded':p['distance']['expanded'],'spatial_local_exact':p['spatial']['local128']['exact'],'spatial_local_expanded':p['spatial']['local128']['expanded'],'spatial_regional_exact':p['spatial']['regional1024']['exact'],'spatial_regional_expanded':p['spatial']['regional1024']['expanded'],'spatial_whole_exact':p['spatial']['whole_corpus']['exact'],'spatial_whole_expanded':p['spatial']['whole_corpus']['expanded']}
        for k,v in vals.items(): assert close(row[k],v), f'exclusion source CSV mismatch {row["source_book"]}/{k}'
    with (ROOT/'results/sensitivity/exclusion_traditional_books_24.csv').open(encoding='utf-8',newline='') as f: tr=list(csv.DictReader(f))
    assert len(tr)==24
    for row,x in zip(tr,sens['exclusion_reporting_24']):
        assert row['traditional_book']==x['traditional_book'] and int(row['source_books'])==x['source_books'] and int(row['words'])==x['words'] and int(row['sound_units'])==x['sound_units']
        for k in ('coverage_exact','coverage_expanded','distance_exact','distance_expanded','spatial_local_exact','spatial_local_expanded','spatial_regional_exact','spatial_regional_expanded','spatial_whole_exact','spatial_whole_expanded'):
            assert close(row[k],x[k]), f'exclusion 24 CSV mismatch {row["traditional_book"]}/{k}'
    with (ROOT/'results/sensitivity/aramaic_only_descriptive.csv').open(encoding='utf-8',newline='') as f: ar=list(csv.DictReader(f))
    assert len(ar)==4
    for row in ar:
        x=sens['affected_books'][row['source_book']]['aramaic_only']; p=x['primary']
        assert int(row['words'])==x['words'] and int(row['sound_units'])==x['sounds'] and int(row['runs'])==x['runs'] and row['full_grid_fnv1a64']==x['hash']
        vals={'coverage_exact':p['coverage']['exact'],'coverage_expanded':p['coverage']['expanded'],'distance_exact':p['distance']['exact'],'distance_expanded':p['distance']['expanded'],'spatial_local_exact':p['spatial']['local128']['exact'],'spatial_local_expanded':p['spatial']['local128']['expanded'],'spatial_regional_exact':p['spatial']['regional1024']['exact'],'spatial_regional_expanded':p['spatial']['regional1024']['expanded'],'spatial_whole_exact':p['spatial']['whole_corpus']['exact'],'spatial_whole_expanded':p['spatial']['whole_corpus']['expanded']}
        for k,v in vals.items(): assert close(row[k],v), f'Aramaic-only CSV mismatch {row["source_book"]}/{k}'
    # No internal temporary/audit debris or Cyrillic working notes.
    forbidden_name=re.compile(r'(audit|pending|stage[1-4])',re.I)
    text_ext={'.py','.md','.json','.csv','.cff','.yml','.yaml','.txt','.bat'}
    for p in ROOT.rglob('*'):
        if not p.is_file(): continue
        rel=p.relative_to(ROOT).as_posix()
        if rel=='CHECKSUMS.json': continue
        if forbidden_name.search(rel): raise AssertionError(f'internal/temporary filename in release: {rel}')
        if p.suffix.lower() in text_ext or p.name in {'LICENSE','VERSION','.gitignore','.gitattributes'}:
            txt=p.read_text(encoding='utf-8',errors='strict')
            if re.search('[\u0400-\u04FF]',txt): raise AssertionError(f'Cyrillic working text in release: {rel}')
    for p in (ROOT/'src').glob('*.py'): py_compile.compile(str(p),doraise=True)
    for p in (ROOT/'src'/'core').glob('*.py'): py_compile.compile(str(p),doraise=True)
    # Windows launchers are CRLF and have no bare LF.
    for p in (ROOT/'run').glob('*.bat'):
        data=p.read_bytes(); assert b'\r\n' in data and data.replace(b'\r\n',b'').find(b'\n')<0, f'bad BAT EOL: {p.name}'
    print(f'PASS checksums: {len(manifest["files"])}')
    print('PASS source/preparation/primary/sensitivity continuity: 39 source-books / 24 traditional books')
    print('PASS frozen totals: 305,584 words / 1,602,109 sound units')
    print('PASS base core blob continuity: 3/3')
    print('PASS primary result CSV regression: 39/39')
    print('PASS Aramaic-sensitivity CSV regression: 39 source-books / 24 reporting books / 4 Aramaic-only rows')
    print('PASS release hygiene: no temporary/audit filenames; no Cyrillic working text')
    print('PASS Python compilation and Windows launcher EOL checks')
if __name__=='__main__': main()
