import json,statistics,random,gzip,hashlib
from pathlib import Path
from collections import defaultdict
P=Path(__file__).resolve().parents[2]; V=set('aeiou')
raw=json.loads((P/'results/corpus/segments.json').read_text(encoding='utf-8'))
def motifs(s):return {tuple(s[i:i+3]) for i in range(len(s)-2) if 0<sum(x in V for x in s[i:i+3])<3}
def dice(a,b):return 2*len(a&b)/(len(a)+len(b)) if a or b else 0.
def main(data=None,outdir=None):
 data=raw if data is None else data
 outdir=P/'results/analysis' if outdir is None else Path(outdir)
 out=[];records=[]
 for cap,length in [(256,512),(1024,1280),(4096,4352)]:
  gaps=[g for g in [0,64,256,1024,4096] if g<=cap]
  for offset in [0,length//2]:
   for phase in [0,64]:
    for corpus in dict.fromkeys(r['corpus'] for r in data):
     tiles=[]
     for seg in data:
      if seg['corpus']!=corpus:continue
      s=seg['sounds']
      for start in range(offset,len(s)-length+1,length):
       vals=[]
       for i in range(start+phase,start+length-128-cap+1,128):
        a=motifs(s[i:i+64]);v=[dice(a,motifs(s[i+64+g:i+128+g])) for g in gaps];vals.append(v)
        records.append([corpus,cap,offset,phase,seg['segment'],start,i,v])
       means=[statistics.mean(v[k] for v in vals) for k in range(len(gaps))]
       tiles.append({'segment':seg['segment'],'start':start,'means':means,'delta':means[0]-means[-1]})
     n=len(tiles);ds=[t['delta'] for t in tiles]
     # Finite-corpus tile resampling: describes sensitivity to tile selection, not a population CI.
     rng=random.Random(2026102207)
     boots=sorted(statistics.mean(rng.choices(ds,k=n)) for _ in range(1000)) if ds else []
     out.append(dict(corpus=corpus,cap=cap,tile_length=length,offset=offset,phase=phase,tiles=n,units_in_tiles=n*length,means={str(g):statistics.mean(t['means'][i] for t in tiles) if n else None for i,g in enumerate(gaps)},delta=statistics.mean(ds) if n else None,resampling_025=boots[24] if n else None,resampling_975=boots[974] if n else None,tile_details=tiles))
 outdir.mkdir(parents=True,exist_ok=True)
 (outdir/'matched.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
 # The published gzip stream has format metadata (including an original timestamp).
 # Rebuild detailed pairs into untracked local outputs instead of modifying its frozen bytes.
 pairs_dir = P/'.local/analysis' if outdir.resolve()==(P/'results/analysis').resolve() else outdir
 pairs_dir.mkdir(parents=True,exist_ok=True)
 with gzip.open(pairs_dir/'matched_pairs.jsonl.gz','wt',encoding='utf-8',newline='\n') as f:
  for r in records:f.write(json.dumps(r)+'\n')
 for r in out:
  if r['cap']==1024:print(r['corpus'],r['offset'],r['phase'],r['tiles'],round(r['delta'],6) if r['delta'] is not None else None)
if __name__=='__main__':main()
