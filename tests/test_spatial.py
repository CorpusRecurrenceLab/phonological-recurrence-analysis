import sys,unittest,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/analysis'))
from spatial import fragment,score
class SpatialTests(unittest.TestCase):
 def test_against_exhaustive_pairs(self):
  rng=random.Random(17)
  for trial in range(5):
   fs=[fragment([[rng.choice(['a','b','e','k']) for _ in range(4)] for j in range(8)]) for i in range(4)]
   occ=[];pos=0
   for n,items in fs:occ.extend((t,pos+i) for t,i in items);pos+=n
   marked=set()
   for t,i in occ:
    for u,j in occ:
     if t==u and 3<=abs(i-j)<=64:marked.update(range(i,i+3))
   self.assertEqual(score(fs,list(range(len(fs)))),(len(marked),pos))
 def test_no_junction_motifs(self):
  fs=[fragment([['a','b']]),fragment([['a','b']]),fragment([['a','b']])]
  self.assertEqual(score(fs,[0,1,2]),(0,6))
if __name__=='__main__':unittest.main()
