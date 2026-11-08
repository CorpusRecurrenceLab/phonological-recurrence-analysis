#!/usr/bin/env python3
"""Independently check the 39 pinned complete-Tanakh source files."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
FREEZE=json.loads((ROOT/'config/tanakh/source_freeze.json').read_text(encoding='utf-8'))
PREP=json.loads((ROOT/'config/tanakh/preparation_expected.json').read_text(encoding='utf-8'))
def blob(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def slug(x):
    import re
    return re.sub(r'[^a-z0-9]+','_',x.lower()).strip('_')
def main():
    found=bad=0
    for entry in FREEZE['source_books']:
        name=entry['source_book']
        path=ROOT/'sources/original/tanakh'/f"{entry['order']:02d}_{slug(name)}.json"
        if not path.is_file():
            status='NOT BUNDLED'
        else:
            actual=blob(path.read_bytes()); status='VERIFIED' if actual==entry['git_blob_sha1'] else 'HASH MISMATCH'
            if status=='VERIFIED':found+=1
            else:bad+=1
        print(f"{entry['order']:02d}/39 {name}: {status}")
    print(f"Frozen source files physically present and hash-verified: {found}/39; invalid: {bad}")
    print('Separate comparison source variants and output CSVs are NOT counted as canonical Tanakh sources.')
    return 1 if bad else 0
if __name__=='__main__':sys.exit(main())
