#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
TW=ROOT
OVERLAP=('Genesis','Exodus','Leviticus','Numbers','Deuteronomy','Joshua','Judges','Psalms','Job','Song_of_Songs')

def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def close(a,b): return math.isclose(float(a),float(b),rel_tol=1e-12,abs_tol=1e-12)

def main():
    # One canonical phonological core, checked against frozen Git blobs.
    import json
    freeze=json.loads((ROOT/'config/tanakh/base_code_freeze.json').read_text(encoding='utf-8'))
    for item in freeze['files']:
        p=ROOT/item['upstream_path']; data=p.read_bytes()
        blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        assert blob==item['git_blob_sha1'], f'frozen core changed: {p}'
    old={}
    with (ROOT/'results/controls/fifteen_work_primary_summary.csv').open(encoding='utf-8',newline='') as f:
        for r in csv.DictReader(f):
            if r['corpus'] in OVERLAP:
                old[(r['corpus'],r['mode'])]=r
    new={}
    with (ROOT/'results/tanakh/primary/source_books_39.csv').open(encoding='utf-8',newline='') as f:
        for r in csv.DictReader(f): new[r['source_book']]=r

    rows=[]
    for book in OVERLAP:
        nb='Song of Songs' if book=='Song_of_Songs' else book
        assert nb in new, f'missing Tanakh-wide book: {nb}'
        for mode in ('exact','expanded'):
            o=old[(book,mode)]; n=new[nb]
            vals=[
              ('coverage_R64',o['coverage_512_offset0_R64'],n[f'coverage_{mode}']),
              ('distance_gap1024',o['distance_adjacent_minus_gap1024_mean4'],n[f'distance_{mode}']),
              ('spatial_local_R64',o['spatial_local128_R64_delta'],n[f'spatial_local_{mode}']),
            ]
            for metric,a,b in vals:
                ok=close(a,b)
                assert ok, f'overlap mismatch {book} {mode} {metric}: {a} != {b}'
                rows.append({'book':nb,'mode':mode,'metric':metric,'earlier_value':a,'tanakh_wide_value':b,'absolute_difference':f'{abs(float(a)-float(b)):.17g}'})

    out=ROOT/'results/integration/cross_layer_regression.csv'; out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n'); w.writeheader(); w.writerows(rows)
    print(f'PASS canonical computational core: 3/3 frozen Git blobs')
    print(f'PASS cross-layer primary regression: {len(rows)}/{len(rows)} values across 10 Biblical books')

if __name__=='__main__': main()
