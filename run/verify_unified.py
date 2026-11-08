#!/usr/bin/env python3
"""Offline unified release verification (no web calls)."""
from pathlib import Path
import csv,hashlib,json,subprocess,sys
R=Path(__file__).resolve().parent.parent

def cmd(*args):
    subprocess.run([sys.executable,*map(str,args)],cwd=R,check=True)

def main():
    cmd('run/project.py','verify')
    cmd('-m','unittest','discover','-s','tests','-q')
    cmd('-m','unittest','discover','-s','tests/tanakh','-q')
    cmd('src/analysis/validate_controls.py')
    cmd('run/tanakh.py','verify')
    cmd('run/tanakh.py','sources')
    cmd('src/analysis/validate_integration.py')
    with (R/'results/comparison/tanakh_and_modern_44_work_descriptive.csv').open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    assert len(rows)==88
    assert sum(x['group']=='tanakh_source_book' for x in rows)==78
    assert sum(x['group']=='modern_comparison' for x in rows)==10
    assert len({x['corpus'] for x in rows})==44
    print('PASS descriptive 44-work table: 39 Tanakh + 5 modern; exact and expanded')
    print('PASS unified offline verification')
if __name__=='__main__': main()
