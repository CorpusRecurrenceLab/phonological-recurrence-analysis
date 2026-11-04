import unittest,json
from pathlib import Path
class MapDirect(unittest.TestCase):
 def test_direct_90(self):
  p=Path(__file__).resolve().parents[1];read=json.loads((p/'reference/readings.json').read_text(encoding='utf-8'));maps={(x['ref'],x['radius']):x for x in json.loads((p/'reference/verse_map.json').read_text(encoding='utf-8'))};V=set('aeiou');pairs={frozenset(x) for x in [('f','v'),('p','b'),('d','t'),('b','v'),('z','s'),('h','kh'),('q','k')]};n=0
  for book in ['Genesis','Exodus','Leviticus','Numbers','Deuteronomy']:
   vs=[x for x in read if x['ref'].startswith(book+' ')];seq=[];bounds=[]
   for x in vs:
    a=len(seq);seq+=x['sounds'];bounds.append((a,len(seq),x['ref']))
   for idx in [0,len(vs)//2,len(vs)-1]:
    a,b,ref=bounds[idx]
    for radius in [32,64,128]:
     for mode in ['exact','expanded']:
      marks=set()
      for i in range(max(0,a-2),min(b,len(seq)-2)):
       t=seq[i:i+3]
       if not 0<sum(u in V for u in t)<3:continue
       for j in range(max(0,i-radius),min(len(seq)-2,i+radius+1)):
        if abs(i-j)<3:continue
        diff=[(x,y) for x,y in zip(t,seq[j:j+3]) if x!=y]
        if not diff or (mode=='expanded' and len(diff)==1 and frozenset(diff[0]) in pairs):marks.update(range(max(a,i),min(b,i+3)));break
      self.assertEqual(len(marks)/(b-a),maps[(ref,radius)][mode]);n+=1
  self.assertEqual(n,90)
