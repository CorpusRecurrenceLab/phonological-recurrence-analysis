"""Build compact published summaries for the pinned comparator controls."""
import csv,statistics
from pathlib import Path
P=Path(__file__).resolve().parents[2];E=P/'results/controls';C=P/'results/comparison'
def read(p):
 with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def write(p,rows):
 with p.open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
coverage=read(C/'coverage.csv')+read(E/'poetic_coverage.csv')
distance=read(C/'distance.csv')+read(E/'poetic_distance.csv')
sp_old=read(C/'spatial.csv');sp_new=read(E/'poetic_spatial.csv')
order=[]
for r in coverage:
 if r['corpus'] not in order:order.append(r['corpus'])
out=[]
for c in order:
 for mode in ('exact','expanded'):
  cv=next(r for r in coverage if r['corpus']==c and r['mode']==mode and r['block']=='512' and r['offset']=='0' and r['radius']=='64')
  dd=[r for r in distance if r['corpus']==c and r['mode']==mode and r['cap']=='1024']
  groups={}
  for r in dd:groups.setdefault((r['offset'],r['phase']),{})[r['gap']]=float(r['mean'])
  delta=statistics.mean(v['0']-v['1024'] for v in groups.values())
  if c in {r['corpus'] for r in sp_old}:
   sr=next(r for r in sp_old if r['corpus']==c and r['mode']==mode and r['radius']=='64' and r['control']=='local128')
  else:
   sr=next(r for r in sp_new if r['corpus']==c and r['condition']==mode and r['radius']=='64' and r['control']=='local128')
  out.append(dict(corpus=c,mode=mode,coverage_512_offset0_R64=float(cv['mean']),distance_adjacent_minus_gap1024_mean4=delta,spatial_local128_R64_delta=float(sr['delta'])))
write(E/'fifteen_work_primary_summary.csv',out)

w=read(E/'different_surface_coverage.csv');s=read(E/'different_surface_spatial.csv');rows=[]
for c in dict.fromkeys(r['corpus'] for r in w):
 a={r['condition']:r for r in w if r['corpus']==c and r['block']=='512' and r['offset']=='0' and r['radius']=='64'}
 b={r['condition']:r for r in s if r['corpus']==c and r['radius']=='64' and r['control']=='local128'}
 rows.append(dict(corpus=c,baseline_coverage=float(a['baseline_exact']['mean']),different_surface_coverage=float(a['different_surface_word']['mean']),coverage_change=float(a['different_surface_word']['mean'])-float(a['baseline_exact']['mean']),baseline_spatial_delta=float(b['baseline_exact']['delta']),different_surface_spatial_delta=float(b['different_surface_word']['delta'])))
write(E/'different_surface_primary_summary.csv',rows)
print('PASS comparator summaries:',len(out),'fifteen-work mode rows;',len(rows),'word-control corpora')
