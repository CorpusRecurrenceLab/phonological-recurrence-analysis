"""Offline assembly and deterministic review sample; no API calls or corrections."""
import argparse, collections, hashlib, json, random, unicodedata, zipfile
from pathlib import Path

def sha(b): return hashlib.sha256(b).hexdigest()
def plain(s):
    return ''.join(c for c in unicodedata.normalize('NFD',s) if not ('\u0591'<=c<='\u05bd' or c in '\u05bf\u05c1\u05c2\u05c4\u05c5\u05c7'))
def require(ok,msg):
    if not ok: raise ValueError(msg)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,default=Path(__file__).resolve().parents[2]/'data/data_processed/modern/benyehuda');ap.add_argument('--archive',type=Path);a=ap.parse_args()
    z=zipfile.ZipFile(a.archive) if a.archive else None
    def read(rel): return z.read('nakdan_output/'+rel) if z else (a.base/'nakdan_output'/rel).read_bytes()
    summary=json.loads(read('summary.json'));require(summary['status']=='ACQUISITION_COMPLETE_REVIEW_REQUIRED','Acquisition incomplete')
    dest=a.base/'nakdan_review';dest.mkdir(exist_ok=True)
    def save(name,obj): (dest/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    total={};seen=set()
    for wid in ('523','7924'):
        m=json.loads((a.base/'nakdan_batches'/wid/'manifest.json').read_text(encoding='utf-8'))
        src=(a.base/'normalized'/f'{wid}.txt').read_text(encoding='utf-8');structure=json.loads((a.base/'normalized'/f'{wid}.json').read_text(encoding='utf-8'))
        require(sha(src.encode())==structure['sha256'],'Normalized source mismatch')
        texts=[];tokens=[];flags=[];changes=[];mapping={0:0};so=co=0
        for ch in m['chunks']:
            entries=[e for e in summary['chunks'] if e['work_id']==wid and e['chunk']==ch['file']];require(len(entries)==1,'Missing/duplicate chunk')
            folder=entries[0]['folder'].replace('\\','/');require(folder.startswith('nakdan_output/'),'Unexpected folder')
            folder=folder[len('nakdan_output/'):];require('..' not in Path(folder).parts,'Unsafe folder');seen.add((wid,ch['file']))
            inp=(a.base/'nakdan_batches'/wid/ch['file']).read_bytes();s=inp.decode();require(sha(inp)==ch['sha256'],'Input hash mismatch');require(ch['start']==so and src[so:so+len(s)]==s,'Chunk order mismatch')
            r=json.loads(read(folder+'/review.json'));q=json.loads(read(folder+'/request.json'));raw=read(folder+'/response.json');response=json.loads(raw)
            require(r['input_sha256']==q['input_sha256']==sha(inp),'Input provenance mismatch');require(r['response_sha256']==q['response_sha256']==sha(raw),'Response hash mismatch');require(r['parameters']==q['parameters'],'Parameters mismatch')
            require(''.join(t['str'] for t in response['data'])==s,'Response input reconstruction mismatch')
            local=[]
            for i,t in enumerate(response['data']):
                w=t['str'] if t['sep'] else t['nakdan']['options'][0]['w'].replace('|','')
                if plain(t['str'])!=plain(w):
                    require(plain(t['str']).replace('\u00ad','')==plain(w),'Unexpected text alteration')
                    changes.append(dict(chunk=ch['file'],source_start=so,source=t['str'],candidate=w,kind='soft_hyphen_removed'))
                row=dict(chunk=ch['file'],token=i,source_start=so,candidate_start=co,source=t['str'],candidate=w)
                if not t['sep']: tokens.append(row)
                mapping[so]=co
                # Structural positions inside separators map directly; words must not be split.
                if t['sep']:
                    for j in range(len(w)+1):mapping[so+j]=co+j
                so+=len(t['str']);co+=len(w);mapping[so]=co;local.append(w)
            rendered=''.join(local);require(rendered.encode()==read(folder+'/candidate.txt'),'Candidate mismatch');texts.append(rendered)
            flags.extend(dict(chunk=ch['file'],**f) for f in r['review_flags'])
        require(so==len(src),'Incomplete source')
        bounds=[]
        for b in structure['boundaries']:
            require(b['offset'] in mapping,'Boundary inside changed token')
            bounds.append(dict(b,source_offset=b['offset'],offset=mapping[b['offset']]))
        text=''.join(texts);(dest/f'{wid}_candidate.txt').write_text(text,encoding='utf-8',newline='\n')
        save(f'{wid}_structure.json',dict(status='REVIEW_REQUIRED',boundaries=bounds,source_sha256=sha(src.encode()),candidate_sha256=sha(text.encode())))
        save(f'{wid}_flags.json',flags);save(f'{wid}_text_changes.json',changes)
        # 20 non-overlapping word-token blocks, 10 tokens each, across 10 equal token strata.
        rng=random.Random(20261002+int(wid));sample=[]
        for stratum in range(10):
            lo=len(tokens)*stratum//10;hi=len(tokens)*(stratum+1)//10
            candidates=list(range(lo,hi-9,10));starts=rng.sample(candidates,min(2,len(candidates)))
            for start in sorted(starts):
                group=tokens[start:start+10];left=group[0]['candidate_start'];last=group[-1];right=last['candidate_start']+len(last['candidate'])
                sample.append(dict(stratum=stratum+1,tokens=group,context=text[max(0,left-160):min(len(text),right+160)],verdict='PENDING',notes=''))
        save(f'{wid}_sample.json',sample)
        total[wid]=dict(chunks=len(m['chunks']),word_tokens=len(tokens),flagged_tokens=len(flags),soft_hyphen_removals=len(changes),boundaries=len(bounds),sample_tokens=sum(len(s['tokens']) for s in sample),status='REVIEW_REQUIRED')
    require(len(seen)==len(summary['chunks']),'Unexpected summary entries')
    save('assembly_summary.json',total);print(json.dumps(total,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
