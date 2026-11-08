"""Guard against accidentally importing src/prepare.py as Tanakh prepare."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TANAKH_DIR = ROOT / 'src' / 'tanakh'


class TanakhImportResolutionTests(unittest.TestCase):
    def test_primary_loads_tanakh_prepare(self):
        sys.path.insert(0, str(TANAKH_DIR))
        try:
            import primary
            self.assertEqual(Path(primary.s2.__file__).resolve(), TANAKH_DIR / 'prepare.py')
            self.assertEqual(primary.s2.safe_slug('I Samuel'), 'i_samuel')
        finally:
            sys.path.remove(str(TANAKH_DIR))

    def test_aramaic_uses_same_module(self):
        sys.path.insert(0, str(TANAKH_DIR))
        try:
            import aramaic_sensitivity
            self.assertEqual(Path(aramaic_sensitivity.s3.s2.__file__).resolve(), TANAKH_DIR / 'prepare.py')
        finally:
            sys.path.remove(str(TANAKH_DIR))
