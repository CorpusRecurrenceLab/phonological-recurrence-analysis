"""Small regression checks for the Tanakh-wide lexical sensitivity release."""
import csv,unittest,sys
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class TanakhWordControlTests(unittest.TestCase):
    def test_checkpoint_fingerprint_includes_active_code_and_rules(self):
        sys.path.insert(0,str(ROOT/'run'))
        try:
            import tanakh_word_control as wc
            fixed=wc.prepare.load_json('config/tanakh/source_freeze.json')['source_books'][0]
            paths=set(wc.FINGERPRINT_INPUTS)
            self.assertIn('src/analysis/poetic_comparators.py',paths)
            self.assertIn('src/tanakh/primary.py',paths)
            self.assertIn('config/tanakh/ketiv_without_qere.json',paths)
            signature=wc.fingerprint(fixed)
            original=wc.Path.read_bytes
            target=ROOT/'src/analysis/poetic_comparators.py'
            def modified(path):
                contents=original(path)
                return contents+b'\n# modified' if path==target else contents
            with patch.object(wc.Path,'read_bytes',modified):
                self.assertNotEqual(signature,wc.fingerprint(fixed))
        finally:
            sys.path.pop(0)

    def test_validator_accepts_recomputed_integer_radii(self):
        # CSV fields are strings; fresh calculations return integer radii.
        # Both representations must trigger all 117 primary cross-checks.
        sys.path.insert(0,str(ROOT/'run'))
        try:
            import tanakh_word_control as wc
            spatial=wc.read(wc.OUT/'different_surface_spatial.csv')
            replicates=wc.read(wc.OUT/'different_surface_spatial_replicates.csv')
            coverage=wc.read(wc.OUT/'different_surface_coverage_summary.csv')
            for row in spatial:
                row['radius']=int(row['radius'])
            for row in replicates:
                row['radius']=int(row['radius'])
            wc.validate(spatial,replicates,coverage)
        finally:
            sys.path.pop(0)

    def test_complete_fixed_geometry(self):
        with (ROOT/'results/tanakh/word_control/different_surface_spatial.csv').open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),702)
        self.assertEqual(len(set(r['corpus'] for r in rows)),39)
        self.assertEqual(set(r['condition'] for r in rows),{'baseline_exact','different_surface_word'})
        self.assertEqual(set(r['control'] for r in rows),{'local128','regional1024','whole_corpus'})
        self.assertEqual(set(r['radius'] for r in rows),{'32','64','128'})

    def test_replicate_count(self):
        with (ROOT/'results/tanakh/word_control/different_surface_spatial_replicates.csv').open(newline='',encoding='utf-8') as f:rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),13338)
        self.assertEqual(set(r['replicate'] for r in rows),set(map(str,range(19))))

    def test_word_coverage(self):
        with (ROOT/'results/tanakh/word_control/different_surface_coverage_summary.csv').open(newline='',encoding='utf-8') as f:rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),39)
        self.assertTrue(all(0<float(r['different_surface_coverage_R64'])<float(r['baseline_coverage_R64'])<1 for r in rows))

if __name__=='__main__':unittest.main()
