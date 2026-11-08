import json,bisect,statistics,random
from pathlib import Path
from collections import defaultdict
P=Path(__file__).resolve().parents[2];V=set('aeiou')
def coverage(s,radius):
 occ=defaultdict(list);marks=bytearray(len(s))
 for i in range(len(s)-2):
  t=tuple(s[i:i+3])
  if 0<sum(c in V for c in t)<3:occ[t].append(i)
 for positions in occ.values():
  for i in positions:
   lo=bisect.bisect_left(positions,i-radius);hi=bisect.bisect_right(positions,i+radius)
   if any(abs(i-j)>=3 for j in positions[lo:hi]):marks[i:i+3]=b'\1\1\1'
 return sum(marks)/len(s),marks
def main(length=1280,source="segments.json",suffix=""):
 raw=json.loads((P/'results/corpus'/source).read_text(encoding='utf-8'));out=[];checks=[]
 for offset in [0,length//2]:
  for corpus in dict.fromkeys(s['corpus'] for s in raw):
   vals={r:[] for r in [32,64,128]}
   for seg in raw:
    if seg['corpus']!=corpus:continue
    for start in range(offset,len(seg['sounds'])-length+1,length):
     seq=seg['sounds'][start:start+length]
     for radius in vals:
      value,_=coverage(seq,radius);vals[radius].append(value)
   for radius,v in vals.items():out.append(dict(tile_length=length,corpus=corpus,offset=offset,radius=radius,tiles=len(v),mean=statistics.mean(v) if v else None,median=statistics.median(v) if v else None,values=v))
 # Independent direct comparison for 20 fixed 150-unit snippets, all radii.
 rng=random.Random(2026102208)
 for seg in rng.sample(raw,20):
  s=seg['sounds'][:150]
  for radius in [32,64,128]:
   found=set()
   for i in range(len(s)-2):
    t=s[i:i+3]
    if not 0<sum(c in V for c in t)<3:continue
    for j in range(max(0,i-radius),min(len(s)-2,i+radius+1)):
     if abs(i-j)>=3 and t==s[j:j+3]:found.update(range(i,i+3))
   _,marks=coverage(s,radius);assert len(found)==sum(marks)
   checks.append([seg['corpus'],seg['segment'],radius])
 (P/f'results/analysis/coverage_matched_{length}{suffix}.json').write_text(json.dumps(out,indent=2),encoding='utf-8',newline='\n')
 (P/f'results/analysis/coverage_verification_{length}{suffix}.json').write_text(json.dumps({'independent_checks':len(checks),'status':'PASS'}),encoding='utf-8',newline='\n')
if __name__=='__main__':
 main(1280)
 main(512)
