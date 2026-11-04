import sys,unittest,random,itertools
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/analysis'))
from compare_modes import variants,occurrences,coverage_counts,similarity,PAIRS,RADII

def near(a,b):
 differences=[(x,y) for x,y in zip(a,b) if x!=y]
 return not differences or len(differences)==1 and (differences[0] in PAIRS or differences[0][::-1] in PAIRS)
class ComparisonTests(unittest.TestCase):
 def test_rules(self):
  self.assertNotIn(('v','a','t'),variants(('p','a','t')))
  self.assertNotIn(('b','a','d'),variants(('p','a','t')))
  self.assertNotIn(('p','e','t'),variants(('p','a','t')))
  self.assertIn(('b','a','t'),variants(('p','a','t')))
 def test_coverage_brute(self):
  rng=random.Random(1)
  for _ in range(20):
   s=[rng.choice(['a','e','t','d','p','b','v']) for _ in range(100)];items=occurrences(s);expected=[]
   for mode in range(2):
    row=[]
    for r in RADII:
     covered=set()
     for a,i in items:
      for b,j in items:
       if 3<=abs(i-j)<=r and (near(a,b) if mode else a==b):covered.update(range(i,i+3))
     row.append(len(covered))
    expected.append(row)
   self.assertEqual(coverage_counts(len(s),items),expected)
 def test_matching_brute(self):
  motifs=[('p','a','t'),('b','a','t'),('v','a','t'),('p','a','d'),('f','a','t')]
  sets=[set(x) for n in range(1,5) for x in itertools.combinations(motifs,n)]
  def brute(a,b):
   if not a:return 0
   x,*rest=a
   return max([brute(rest,b)]+[1+brute(rest,b-{y}) for y in b if near(x,y)])
  for a in sets:
   for b in sets:self.assertEqual(similarity(a,b)[1],2*brute(list(a),b)/(len(a)+len(b)))
 def test_no_double_count(self):
  a={('p','a','t'),('v','a','t')};b={('b','a','t')}
  self.assertEqual(similarity(a,b),(0.,2/3))
