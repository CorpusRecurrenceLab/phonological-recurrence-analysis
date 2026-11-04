#!/usr/bin/env python3
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def run(script,*args):
    cmd=[sys.executable,str(ROOT/'src'/script),*args]
    print('+',' '.join(cmd),flush=True)
    subprocess.run(cmd,cwd=ROOT,check=True)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('command',choices=('verify','prepare','primary','sensitivity','all'))
    ap.add_argument('--offline',action='store_true',help='reuse cached pinned source JSON files; do not download')
    a=ap.parse_args()
    if a.command=='verify':
        run('verify_release.py'); return
    if a.command in ('prepare','all'):
        extra=['--offline'] if a.offline else []
        run('prepare.py',*extra)
    if a.command in ('primary','all'):
        run('primary.py')
    if a.command in ('sensitivity','all'):
        run('aramaic_sensitivity.py')
    if a.command=='all': run('verify_release.py')
if __name__=='__main__': main()
