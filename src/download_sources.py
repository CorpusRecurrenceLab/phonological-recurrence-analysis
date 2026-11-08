"""Acquire the ten baseline sources; verify analyzed Hebrew rather than API metadata."""
from __future__ import annotations
import argparse, hashlib, json, urllib.request
from pathlib import Path
P=Path(__file__).resolve().parents[1]
NAMES={'523':'brenner_mikan_umikan','7924':'ahad_haam_shilton_hasekhel','884':'tchernichovsky_hatunata_shel_elka'}
def sha(data):return hashlib.sha256(data).hexdigest()
def rows():return json.loads((P/'config/source_acquisition.json').read_text(encoding='utf-8'))
def frozen_path(row):
    return P/row['bundled_path']
def verify_biblical_response(response,frozen):
    if response.get('heVersionTitle') != frozen['returned_version']:
        raise ValueError('Requested Hebrew edition not returned')
    chapters=response.get('he')
    if not isinstance(chapters,list) or [len(x) for x in chapters] != frozen['chapter_lengths']:
        raise ValueError('Chapter/verse segmentation changed')
    expected={(v['chapter'],v['verse']):v['source_text'] for v in frozen['verses']}
    for ci,ch in enumerate(chapters,1):
        for vi,text in enumerate(ch,1):
            if text != expected[(ci,vi)]:raise ValueError(f'Hebrew source changed at {ci}:{vi}')
def verify_cached():
    for row in rows():
        if sha(frozen_path(row).read_bytes()) != row['bundled_sha256']:
            raise ValueError('Changed bundled source: '+row['bundled_path'])
    print('PASS: ten bundled source hashes')
def download(destination):
    verify_cached();destination.mkdir(parents=True,exist_ok=True);report=[]
    for row in rows():
        with urllib.request.urlopen(row['url'],timeout=60) as response:data=response.read()
        if 'book' in row:
            frozen=json.loads(frozen_path(row).read_text(encoding='utf-8'))
            verify_biblical_response(json.loads(data.decode('utf-8')),frozen)
            # Only the verified Hebrew projection is retained, not unrelated translations or service metadata.
            output=frozen_path(row).read_bytes();name=row['book']+'_verses.json'
        else:
            if sha(data) != row['bundled_sha256']:raise ValueError('Modern source changed: '+row['id'])
            output=data;name=NAMES[row['id']]+'.txt'
        (destination/name).write_bytes(output)
        report.append({'source':row.get('book',row.get('id')),'file':name,'sha256':sha(output),'verification':'PASS'})
    (destination/'download_manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('PASS: ten reacquired source texts')
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=['cached','download'],default='cached')
    parser.add_argument('--destination',type=Path,default=P/'.local/downloads')
    args=parser.parse_args()
    verify_cached() if args.mode=='cached' else download(args.destination)
if __name__=='__main__':main()
