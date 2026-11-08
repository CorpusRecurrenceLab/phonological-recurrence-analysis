"""Independent structural and regression checks for the comparator controls."""
import csv,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[2];E=P/'results/controls'
def rows(p):
 with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def ok(name,v,checks):
 if not v:raise ValueError('Comparator validation failed: '+name)
 checks.append(name)
checks=[]
inv=rows(E/'poetic_comparator_inventory.csv');ok('three preselected poetic comparators',[r['corpus'] for r in inv]==['Psalms','Job','Song_of_Songs'],checks)
ok('Psalms 150 chapters',inv[0]['chapters']=='150',checks);ok('Psalms 2527 verses',inv[0]['verses']=='2527',checks)
ok('Psalms hard boundaries',inv[0]['hard_internal_boundaries']=='149',checks)
ok('Job 42 chapters / 1070 verses',inv[1]['chapters']=='42' and inv[1]['verses']=='1070',checks)
ok('Song 8 chapters / 117 verses',inv[2]['chapters']=='8' and inv[2]['verses']=='117',checks)
# New comparator grids.
cov=rows(E/'poetic_coverage.csv');ok('poetic coverage complete',len(cov)==72 and {r['mode'] for r in cov}=={'exact','expanded'},checks)
dist=rows(E/'poetic_distance.csv');ok('poetic distance nonempty',len(dist)>200,checks)
sp=rows(E/'poetic_spatial.csv');ok('poetic spatial complete',len(sp)==54,checks)
# Word-control grid and monotonicity.
w=rows(E/'different_surface_coverage.csv');ok('thirteen word-control corpora',len({r['corpus'] for r in w})==13,checks)
base={(r['corpus'],r['block'],r['offset'],r['radius']):float(r['mean']) for r in w if r['condition']=='baseline_exact'}
for r in w:
 if r['condition']=='different_surface_word':ok('word coverage monotonic '+str((r['corpus'],r['block'],r['offset'],r['radius'])),float(r['mean'])<=base[(r['corpus'],r['block'],r['offset'],r['radius'])]+1e-15,checks)
# Regression: new baseline exactly reproduces existing 10 distributed-corpus exact grids.
old=rows(P/'results/comparison/coverage.csv');old={(r['corpus'],r['block'],r['offset'],r['radius']):float(r['mean']) for r in old if r['mode']=='exact'}
distributed={'Genesis','Exodus','Leviticus','Numbers','Deuteronomy','Joshua','Judges','modern_523','modern_7924','modern_884'}
count=0
for k,v in base.items():
 if k[0] in distributed:ok('coverage regression '+str(k),abs(v-old[k])<1e-12,checks);count+=1
ok('120 coverage regression checks',count==120,checks)
ws=rows(E/'different_surface_spatial.csv');olds=rows(P/'results/comparison/spatial.csv');olds={(r['corpus'],r['radius'],r['control']):(float(r['observed']),float(r['null_mean']),float(r['delta'])) for r in olds if r['mode']=='exact'};count=0
for r in ws:
 if r['condition']=='baseline_exact' and r['corpus'] in distributed:
  k=(r['corpus'],r['radius'],r['control']);v=(float(r['observed']),float(r['null_mean']),float(r['delta']));ok('spatial regression '+str(k),max(abs(v[i]-olds[k][i]) for i in range(3))<1e-12,checks);count+=1
ok('90 spatial regression checks',count==90,checks)
meta=json.loads((E/'controls_validation.json').read_text(encoding='utf-8'))
for name,digest in meta['outputs'].items():ok('control output hash '+name,hashlib.sha256((E/name).read_bytes()).hexdigest()==digest,checks)
record={'status':'PASS','checks':len(checks),'coverage_regression_checks':120,'spatial_regression_checks':90,'poetic_comparators':3,'word_control_corpora':13}
(P/'.local/validation/extension.json').parent.mkdir(parents=True,exist_ok=True);(P/'.local/validation/extension.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print('PASS comparator validation:',len(checks),'checks')
