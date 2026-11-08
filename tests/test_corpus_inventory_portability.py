"""Protect frozen Appendix A from write-before-verify mistakes."""
import csv
import importlib.util
import io
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'src/analysis/corpus_inventory.py'
spec = importlib.util.spec_from_file_location('corpus_inventory_portability', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class InventoryPortabilityTests(unittest.TestCase):
    def test_frozen_inventory_not_opened_for_writing(self):
        source = SCRIPT.read_text(encoding='utf-8')
        self.assertNotIn('FROZEN.open("w"', source)
        self.assertNotIn('FROZEN.write_text(', source)
        self.assertIn('GENERATED.open("w"', source)

    def test_frozen_inventory_is_lf(self):
        raw = (ROOT / 'results/corpus_inventory.csv').read_bytes()
        self.assertNotIn(b'\r', raw)
        self.assertEqual(raw.count(b'\n'), 13)

    def test_additional_corpora_count_units_not_characters(self):
        # The old code counted len("sh") == 2, inflating the two
        # additional-corpus counts by every multigraph phoneme.
        sample = [[["sh", "a", "ts"], ["kh", "o"]], [["b", "e"]]]
        count = sum(len(word) for segment in sample for word in segment)
        self.assertEqual(count, 7)
        self.assertNotEqual(count, sum(len(unit) for segment in sample
                                       for word in segment for unit in word))
        source = SCRIPT.read_text(encoding='utf-8')
        self.assertIn('sum(len(word) for segment in segments for word in segment)', source)
        self.assertNotIn('sum(len(unit) for segment in segments for word in segment for unit in word)', source)

    def test_numerical_cross_platform_tolerance(self):
        one = dict(corpus='a', sound_units=42, spatial_blocks=3,
                   spatial_retained_fraction=0.9, coverage_blocks=5,
                   coverage_retained_fraction=0.8)
        two = {key: str(value) for key, value in one.items()}
        two['spatial_retained_fraction'] = '0.9000000000000001'
        self.assertFalse(module.compare_inventory([one], [two]))
        two['sound_units'] = '43'
        self.assertTrue(module.compare_inventory([one], [two]))


if __name__ == '__main__':
    unittest.main()
