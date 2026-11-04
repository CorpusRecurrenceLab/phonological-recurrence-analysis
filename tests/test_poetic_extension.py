import sys, unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R),str(R/'src'),str(R/'src/analysis')]
from analysis.poetic_extension import motif_occurrences, coverage_counts
from analysis.compare_modes import coverage_counts as legacy_coverage_counts, occurrences as legacy_occurrences

class PoeticExtensionTests(unittest.TestCase):
    def test_psalm_boundary_blocks_cross_boundary_triplet(self):
        words=[('b','a'),('t','a')]
        _,free=motif_occurrences(words,set())
        _,blocked=motif_occurrences(words,{1})
        free_starts={i for t,i,h in free}; blocked_starts={i for t,i,h in blocked}
        self.assertIn(1,free_starts)       # a-t-a crosses the word/psalm boundary
        self.assertNotIn(1,blocked_starts)

    def test_same_surface_host_does_not_qualify(self):
        t=('b','a','t'); h=(('b','a','t'),)
        items=[(t,0,h),(t,10,h)]
        self.assertGreater(coverage_counts(20,items,False,False)[2],0)
        self.assertEqual(coverage_counts(20,items,True,False)[2],0)

    def test_different_surface_host_qualifies(self):
        t=('b','a','t')
        items=[(t,0,(('b','a','t'),)),(t,10,(('b','a','t','a'),))]
        self.assertGreater(coverage_counts(20,items,True,False)[2],0)

    def test_expanded_coverage_matches_frozen_implementation(self):
        s=list('batavadatabafatakhat')*8
        legacy=legacy_occurrences(s)
        items=[(t,i,(('host',str(i)),)) for t,i in legacy]
        got=[coverage_counts(len(s),items,False,False),coverage_counts(len(s),items,False,True)]
        self.assertEqual(got,legacy_coverage_counts(len(s),legacy))

if __name__=='__main__':unittest.main()
