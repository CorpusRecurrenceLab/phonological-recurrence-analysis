"""Release-level tests for deterministic source handling and mismatch rejection."""
import hashlib, json, sys, unittest
from pathlib import Path

R = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(R), str(R / "src" / "preparation")]
import project
from prepare_biblical_reading import adapt as biblical


class ReleaseTests(unittest.TestCase):
    def test_qere_and_marker_logged(self):
        out, edits, spans = biblical('הוא [הִיא] (ס)')
        self.assertEqual(out.strip(), 'הִיא')
        self.assertEqual(len(edits), 2)

    def test_multiword_maqaf_ketiv(self):
        self.assertEqual(biblical('אב־גד [אָב גָּד]')[0], 'אָב גָּד')

    def test_pointed_neighbor_preserved(self):
        self.assertEqual(biblical('אֶת־ידו [יָדָיו]')[0], 'אֶת־יָדָיו')

    def test_unknown_source_markup_stops(self):
        with self.assertRaises(ValueError):
            biblical('<unknown>')

    def test_recursive_comparison_rejects_change(self):
        with self.assertRaises(ValueError):
            project.compare({'x': .1}, {'x': .11})
        with self.assertRaises(ValueError):
            project.compare([{'corpus':'A'}], [{'corpus':'B'}])

    def test_frozen_modern_prepared_hashes(self):
        expected = json.loads((R / 'config' / 'prepared_texts.json').read_text(encoding='utf-8'))
        modern = [p for p in expected if '/brenner_' in p or '/ahad_' in p or '/tchernichovsky_' in p]
        self.assertEqual(len(modern), 3)
        for rel in modern:
            digest = hashlib.sha256((R / rel).read_bytes()).hexdigest()
            self.assertEqual(digest, expected[rel])


if __name__ == '__main__':
    unittest.main()
