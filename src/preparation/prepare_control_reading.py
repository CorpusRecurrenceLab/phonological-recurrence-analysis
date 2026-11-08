"""Prepare a reversible reading layer; does not certify vocalization."""
import argparse,hashlib,json,unicodedata
from pathlib import Path

def sha(b):return hashlib.sha256(b).hexdigest()
def adapt(text,kind):
    groups=[]
    for i,c in enumerate(text):
        if unicodedata.combining(c) and groups:groups[-1][1]+=c
        else:groups.append([i,c])
    drops=set();edits=[]
    if kind=='dicta':
        for i,g in groups:
            if '\u05bd' not in g:continue
            if g[0] not in 'אוי' or g[1:]!='\u05bd':raise ValueError('Unknown Dicta marker form')
            drops.update(range(i,i+len(g)));edits.append(dict(start=i,end=i+len(g),removed=g,reason='Dicta keepmetagim carrier; not biblical stress'))
    elif kind!='original':raise ValueError('Unknown source kind')
    out=[];mapping=[0]
    for i,c in enumerate(text):
        if i not in drops:out.append(c)
        mapping.append(len(out))
    return ''.join(out),mapping,edits

def main():
    p=argparse.ArgumentParser();p.add_argument('--base',type=Path,default=Path(__file__).resolve().parents[2]/'data/data_processed/modern/benyehuda');a=p.parse_args();out=a.base/'reading_layer';out.mkdir(exist_ok=True)
    summary={}
    for wid in ('523','7924','884'):
        kind='original' if wid=='884' else 'dicta'
        input_path=a.base/('normalized' if wid=='884' else 'nakdan_review')/(f'{wid}.txt' if wid=='884' else f'{wid}_candidate.txt')
        meta_path=input_path.with_suffix('.json') if wid=='884' else input_path.with_name(f'{wid}_structure.json')
        raw=input_path.read_bytes();text=raw.decode('utf-8');meta=json.loads(meta_path.read_text(encoding='utf-8'))
        if sha(raw)!=meta['sha256' if wid=='884' else 'candidate_sha256']:raise ValueError('Input hash mismatch')
        result,mapping,edits=adapt(text,kind)
        # Undo every edit to verify reversibility using retained original positions.
        restored=[];ri=0;by_start={e['start']:e for e in edits};i=0
        while i<len(text):
            if i in by_start:
                e=by_start[i];restored.append(e['removed']);i=e['end']
            else:restored.append(result[ri]);ri+=1;i+=1
        if ''.join(restored)!=text or ri!=len(result):raise ValueError('Reconstruction failed')
        bounds=[dict(b,input_offset=b['offset'],offset=mapping[b['offset']]) for b in meta['boundaries']]
        payload=dict(source_kind=kind,input_sha256=sha(raw),output_sha256=sha(result.encode()),status='TECHNICAL_PREPARATION_ONLY',boundaries=bounds,edits=edits,offset_unit='Unicode code point',input_to_output=mapping)
        (out/f'{wid}.txt').write_text(result,encoding='utf-8',newline='\n')
        (out/f'{wid}.json').write_text(json.dumps(payload,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
        summary[wid]=dict(source_kind=kind,removed_carrier_graphemes=len(edits),boundaries=len(bounds),input_characters=len(text),output_characters=len(result),vocalization_certified=False)
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
