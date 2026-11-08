#!/usr/bin/env python3
"""Recompute bundled baseline and 39-book Tanakh layers without network or Nakdan.

This does NOT independently regenerate Rivlin-dependent comparative outputs.
Those are checked against frozen results via verify_unified.py.
"""
from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
STAGES = [
    ("bundled_release_validation", ["run/verify_unified.py"]),
    ("prepare_bundled_baseline", ["run/project.py", "prepare"]),
    ("recompute_bundled_baseline", ["run/project.py", "analyze"]),
    ("recompute_39_book_tanakh", ["run/tanakh.py", "all", "--offline"]),
    ("cross_layer_regression", ["src/analysis/validate_integration.py"]),
    ("word_control_frozen_validation", ["run/tanakh_word_control.py", "--verify"]),
    ("frozen_file_integrity", ["run/project.py", "verify"]),
]

def main():
    completed=[]
    target=ROOT/'.local/validation/reproduction_offline.json'
    target.parent.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ,PYTHONUTF8='1',PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1',HASHIRA_OFFLINE='1')
    try:
        for label,args in STAGES:
            print('Offline stage:',label,flush=True)
            subprocess.run([sys.executable,*args],cwd=ROOT,env=env,check=True)
            completed.append(label)
    finally:
        target.write_text(json.dumps({'status':'PASS' if len(completed)==len(STAGES) else 'INCOMPLETE','completed_stages':completed},indent=2)+'\n',encoding='utf-8')
    print('PASS independent offline rebuild of bundled layers; restricted Rivlin comparisons are frozen-value validated only')

if __name__=='__main__':main()
