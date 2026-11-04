"""Fixed fragment-preserving spatial diagnostic; see protocols/spatial_control.md."""
import json,random,statistics,hashlib,csv,sys,re
from pathlib import Path
from collections import defaultdict,Counter
from bisect import bisect_left,bisect_right
P=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(P/'src'));from prepare import TOKEN
sys.path.insert(0,str(P/'src/core'));from phonetic_core_v2 import transliterate_word
V=set('aeiou')
def words_to_segments(text,bounds):
 out=[];seq=[]
 for a,b in zip(bounds,bounds[1:]):
  for m in TOKEN.finditer(text[a:b]):
   u=transliterate_word(m.group(),return_units=True)
   if u:seq.append(u)
   elif seq:out.append(seq);seq=[]
  if seq:out.append(seq);seq=[]
 return out

def corpus_words(additional=False):
 cfg=json.loads((P/'config/corpora.json').read_text(encoding='utf-8'));out={}
 for name in cfg['biblical']:
  t=(P/f'sources/prepared/{name}/text.txt').read_text(encoding='utf-8');out[name.title()]=words_to_segments(t,[0,len(t)])
 for ident,slug in cfg['modern'].items():
  d=P/'sources/prepared'/slug;t=(d/'text.txt').read_text(encoding='utf-8');meta=json.loads((d/'changes.json').read_text(encoding='utf-8'));bounds=sorted({0,len(t)}|{b['offset'] for b in meta['boundaries']});out['modern_'+ident]=words_to_segments(t,bounds)
 frozen=json.loads((P/'results/corpus/segments.json').read_text(encoding='utf-8'));expected=defaultdict(list)
 for s in frozen:expected[s['corpus']].append(s['sounds'])
 for c,segs in out.items():assert [[u for w in s for u in w] for s in segs]==expected[c],c
 ext=P/'.local/additional/segments_words.json'
 if additional:
  if not ext.exists():raise FileNotFoundError("Run additional_sources.py first")
  out.update(json.loads(ext.read_text(encoding='utf-8')))
 return out

def fragment(ws):
 s=[u for w in ws for u in w];occ=[]
 for i in range(len(s)-2):
  t=tuple(s[i:i+3])
  if 0<sum(x in V for x in t)<3:occ.append((t,i))
 return (len(s),occ)

def score(frags,ids):
 occ=defaultdict(list);pos=0
 for idx in ids:
  length,items=frags[idx]
  for t,i in items:occ[t].append(pos+i)
  pos+=length
 marks=bytearray(pos)
 for positions in occ.values():
  for i in positions:
   lo=bisect_left(positions,i-64);hi=bisect_right(positions,i+64)
   if any(abs(i-j)>=3 for j in positions[lo:hi]):marks[i:i+3]=b'\1\1\1'
 return sum(marks),pos

def evaluate(frags,ids):
 scores=[score(frags,ids[i:i+16]) for i in range(0,len(ids),16)]
 return sum(a for a,b in scores)/sum(b for a,b in scores)

def main():
 out=[];inventory=[]
 for corpus,segs in corpus_words("--additional" in sys.argv).items():
  frags=[];regions=[];total=sum(len(u) for s in segs for u in s)
  for seg in segs:
   first=len(frags);n=len(seg)//128*128
   frags.extend(fragment(seg[i:i+8]) for i in range(0,n,8))
   for st in range(first,len(frags),128):regions.append((st,min(st+128,len(frags))))
  ids=list(range(len(frags)));units=sum(x[0] for x in frags)
  inventory.append(dict(corpus=corpus,blocks=len(frags)//16,total_units=total,retained_units=units,retained_fraction=units/total))
  if not ids:continue
  observed=evaluate(frags,ids)
  for control in ['local128','regional1024','whole_corpus']:
   vals=[]
   for rep in range(19):
    rng=random.Random(2026102601+rep);order=ids.copy()
    ranges=[(i,i+16) for i in range(0,len(ids),16)] if control=='local128' else regions if control=='regional1024' else [(0,len(ids))]
    for a,b in ranges:
     sub=order[a:b];rng.shuffle(sub);order[a:b]=sub
    assert sorted(order)==ids
    vals.append(evaluate(frags,order))
   mu=statistics.mean(vals);row=dict(corpus=corpus,control=control,observed=observed,null_mean=mu,delta=observed-mu,null_min=min(vals),null_max=max(vals),replicates=vals)
   out.append(row);print(corpus,control,round(observed,5),round(mu,5),round(observed-mu,5),flush=True)
 A=P/'results/analysis';A.mkdir(parents=True,exist_ok=True)
 (A/('spatial_concentration_extended.json' if '--additional' in sys.argv else 'spatial_concentration.json')).write_text(json.dumps(dict(protocol_sha256=hashlib.sha256((P/'protocols/spatial_control.md').read_bytes()).hexdigest(),inventory=inventory,results=out),indent=2),encoding='utf-8',newline='\n')
if __name__=='__main__':main()
