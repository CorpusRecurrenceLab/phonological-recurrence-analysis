"""Paired exact / one direct consonant substitution analysis of fixed corpora."""
import bisect,csv,hashlib,json,os,random,statistics
from pathlib import Path
from collections import defaultdict
from functools import lru_cache
from spatial import corpus_words,fragment,P
V=set('aeiou');RADII=(32,64,128)
PAIRS=(('f','v'),('p','b'),('d','t'),('b','v'),('z','s'),('h','kh'),('q','k'))
NEAR=defaultdict(set)
for a,b in PAIRS:NEAR[a].add(b);NEAR[b].add(a)
@lru_cache(None)
def variants(t):return tuple(sorted({t[:i]+(b,)+t[i+1:] for i,a in enumerate(t) for b in NEAR[a]}))
def occurrences(s):return [(tuple(s[i:i+3]),i) for i in range(len(s)-2) if 0<sum(x in V for x in s[i:i+3])<3]
def nearest(ps,i):
 k=bisect.bisect_right(ps,i-3);best=i-ps[k-1] if k else 10**9;k=bisect.bisect_left(ps,i+3)
 return min(best,ps[k]-i if k<len(ps) else 10**9)
def coverage_counts(length,items):
 occ=defaultdict(list)
 for t,i in items:occ[t].append(i)
 marks=[[bytearray(length) for _ in RADII] for _ in range(2)]
 for t,positions in occ.items():
  others=[occ[v] for v in variants(t) if v in occ]
  for i in positions:
   exact=nearest(positions,i);expanded=exact
   for ps in others:expanded=min(expanded,nearest(ps,i))
   for mode,d in enumerate((exact,expanded)):
    for k,r in enumerate(RADII):
     if d<=r:marks[mode][k][i:i+3]=b'\1\1\1'
 return [[sum(m) for m in ms] for ms in marks]
def similarity(a,b):
 den=len(a)+len(b)
 if not den:return 0.,0.
 adj={x:sorted(({x}|set(variants(x)))&b) for x in sorted(a)};matched={}
 def augment(x,seen):
  for y in adj[x]:
   if y in seen:continue
   seen.add(y)
   if y not in matched or augment(matched[y],seen):matched[y]=x;return True
  return False
 for x in adj:augment(x,set())
 return 2*len(a&b)/den,2*len(matched)/den

def write_json(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.pending');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n');os.replace(tmp,path)
def write_csv(path,rows):
 if not rows:return
 tmp=path.with_suffix('.pending')
 with tmp.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
 os.replace(tmp,path)
def compute_coverage(c,segs):
 summary=[];density=[];total=sum(map(len,segs))
 for L in (512,1280):
  for offset in (0,L//2):
   values=defaultdict(list);global_start=0
   for si,s in enumerate(segs):
    for start in range(offset,len(s)-L+1,L):
     counts=coverage_counts(L,occurrences(s[start:start+L]))
     for m,mode in enumerate(('exact','expanded')):
      for k,r in enumerate(RADII):
       val=counts[m][k]/L;values[mode,r].append(val)
       if L==512 and offset==0 and r==64:density.append(dict(corpus=c,mode=mode,segment=si,start=global_start+start,length=L,coverage=val))
    global_start+=len(s)
   for (mode,r),vs in values.items():
    ss=sorted(vs);summary.append(dict(corpus=c,mode=mode,block=L,offset=offset,radius=r,blocks=len(vs),retained_fraction=len(vs)*L/total,mean=statistics.mean(vs),p10=ss[int((len(ss)-1)*.1)],median=statistics.median(vs),p90=ss[int((len(ss)-1)*.9)],minimum=min(vs)))
 return summary,density

def compute_distance(c,segs):
 summary=[];detail=[];total=sum(map(len,segs))
 for cap,L in ((256,512),(1024,1280),(4096,4352)):
  gaps=[g for g in (0,64,256,1024,4096) if g<=cap]
  for offset in (0,L//2):
   for phase in (0,64):
    blocks=defaultdict(list);anchors=0
    for si,s in enumerate(segs):
     @lru_cache(None)
     def motifs(i):return {t for t,_ in occurrences(s[i:i+64])}
     for start in range(offset,len(s)-L+1,L):
      vals=defaultdict(list)
      for i in range(start+phase,start+L-128-cap+1,128):
       anchors+=1
       for gap in gaps:
        scores=similarity(motifs(i),motifs(i+64+gap))
        for m,mode in enumerate(('exact','expanded')):vals[mode,gap].append(scores[m])
      for (mode,gap),vs in vals.items():
       mean=statistics.mean(vs);blocks[mode,gap].append(mean);detail.append(dict(corpus=c,mode=mode,cap=cap,offset=offset,phase=phase,segment=si,start=start,gap=gap,mean=mean))
     motifs.cache_clear()
    for (mode,gap),vs in blocks.items():summary.append(dict(corpus=c,mode=mode,cap=cap,block=L,offset=offset,phase=phase,gap=gap,blocks=len(vs),anchors=anchors,retained_fraction=len(vs)*L/total,mean=statistics.mean(vs)))
 return summary,detail

def compute_spatial(c,wordsegs):
 frags=[];regions=[];total=sum(len(w) for s in wordsegs for w in s)
 for seg in wordsegs:
  first=len(frags);n=len(seg)//128*128;frags.extend(fragment(seg[i:i+8]) for i in range(0,n,8))
  for st in range(first,len(frags),128):regions.append((st,min(st+128,len(frags))))
 ids=list(range(len(frags)));units=sum(x[0] for x in frags)
 def evaluate(order):
  sums=[[0]*3 for _ in range(2)]
  for k in range(0,len(order),16):
   pos=0;items=[]
   for idx in order[k:k+16]:
    length,its=frags[idx];items.extend((t,pos+i) for t,i in its);pos+=length
   v=coverage_counts(pos,items)
   for m in range(2):
    for j in range(3):sums[m][j]+=v[m][j]
  return [[x/units for x in row] for row in sums]
 observed=evaluate(ids);rows=[];reps=[]
 for control in ('local128','regional1024','whole_corpus'):
  vals=[]
  for rep in range(19):
   rng=random.Random(2026102601+rep);order=ids.copy();ranges=[(i,i+16) for i in range(0,len(ids),16)] if control=='local128' else regions if control=='regional1024' else [(0,len(ids))]
   for a,b in ranges:
    sub=order[a:b];rng.shuffle(sub);order[a:b]=sub
   assert sorted(order)==ids
   v=evaluate(order);vals.append(v)
   for m,mode in enumerate(('exact','expanded')):
    for j,r in enumerate(RADII):reps.append(dict(corpus=c,mode=mode,radius=r,control=control,replicate=rep,coverage=v[m][j]))
  for m,mode in enumerate(('exact','expanded')):
   for j,r in enumerate(RADII):
    vs=[v[m][j] for v in vals];mu=statistics.mean(vs);rows.append(dict(corpus=c,mode=mode,radius=r,control=control,blocks=len(ids)//16,retained_fraction=units/total,observed=observed[m][j],null_mean=mu,delta=observed[m][j]-mu,null_min=min(vs),null_max=max(vs)))
 return rows,reps

def validate_exact(rows):
 old=[]
 for p in [P/'results/analysis/coverage_matched_512.json',P/'results/analysis/coverage_matched_1280.json',P/'results/analysis/additional/coverage.json']:old.extend(json.loads(p.read_text(encoding='utf-8')))
 refs={(x['corpus'],x['tile_length'],x['offset'],x['radius']):x for x in old};checks=0
 for x in rows['coverage']:
  if x['mode']=='exact':
   o=refs[x['corpus'],x['block'],x['offset'],x['radius']];assert abs(x['mean']-o['mean'])<1e-12;checks+=1
 old=json.loads((P/'results/analysis/matched.json').read_text(encoding='utf-8'))+json.loads((P/'results/analysis/additional/matched.json').read_text(encoding='utf-8'));refs={(x['corpus'],x['cap'],x['offset'],x['phase']):x for x in old}
 for x in rows['distance']:
  if x['mode']=='exact':
   o=refs[x['corpus'],x['cap'],x['offset'],x['phase']];assert abs(x['mean']-o['means'][str(x['gap'])])<1e-12;checks+=1
 old=json.loads((P/'results/analysis/spatial_concentration_extended.json').read_text(encoding='utf-8'))['results'];refs={(x['corpus'],x['control']):x for x in old}
 for x in rows['spatial']:
  if x['mode']=='exact' and x['radius']==64:
   o=refs[x['corpus'],x['control']]
   for k in ('observed','null_mean','delta'):assert abs(x[k]-o[k])<1e-12;checks+=1
 return checks

def main():
 words=corpus_words(additional=True);out=P/'results/comparison';out.mkdir(exist_ok=True);allrows={k:[] for k in ['coverage','density','distance','distance_blocks','spatial','spatial_replicates']}
 input_hash=hashlib.sha256(json.dumps(words,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest();signature=hashlib.sha256(Path(__file__).read_bytes()+(P/'protocols/exact_expanded_comparison.md').read_bytes()+input_hash.encode()).hexdigest()
 for c,segs in words.items():
  checkpoint=out/'checkpoints'/f'{c}.json';data=json.loads(checkpoint.read_text(encoding='utf-8')) if checkpoint.exists() else {}
  if data.get('signature')!=signature:
   print(c,'calculating',flush=True);soundsegs=[[u for w in s for u in w] for s in segs];cv,density=compute_coverage(c,soundsegs);ds,db=compute_distance(c,soundsegs);sp,reps=compute_spatial(c,segs)
   data=dict(signature=signature,coverage=cv,density=density,distance=ds,distance_blocks=db,spatial=sp,spatial_replicates=reps);write_json(checkpoint,data)
  for k in allrows:allrows[k].extend(data[k])
  print(c,'complete',flush=True)
 for k,v in allrows.items():write_csv(out/f'{k}.csv',v)
 checks=validate_exact(allrows);validation=P/'.local/validation/paired_regression.json';validation.parent.mkdir(parents=True,exist_ok=True);write_json(validation,dict(status='PASS',exact_regression_checks=checks,corpora=len(words),input_sha256=input_hash,protocol_sha256=hashlib.sha256((P/'protocols/exact_expanded_comparison.md').read_bytes()).hexdigest(),code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()));print('PASS exact regression checks:',checks,flush=True)
if __name__=='__main__':main()
