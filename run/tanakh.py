#!/usr/bin/env python3
"""Tanakh corpus entry point using one canonical phonological core."""
from __future__ import annotations
import argparse,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def run(script,*args):
    env=dict(os.environ,PYTHONUTF8='1',PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1')
    command=[sys.executable,str(ROOT/'src/tanakh'/script),*args]
    print('+',' '.join(command),flush=True)
    subprocess.run(command,cwd=ROOT,check=True,env=env)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('command',choices=('verify','prepare','primary','sensitivity','all','sources'))
    ap.add_argument('--offline',action='store_true')
    args=ap.parse_args()
    if args.command == 'sources':run('source_inventory.py');return
    if args.command in ('prepare','all'):run('prepare.py','--publish-sources',*(['--offline'] if args.offline else []))
    if args.command in ('primary','all'):run('primary.py')
    if args.command in ('sensitivity','all'):run('aramaic_sensitivity.py')
    if args.command in ('verify','all'):run('verify_release.py')
if __name__=='__main__':main()
