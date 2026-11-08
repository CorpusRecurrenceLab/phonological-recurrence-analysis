"""Cross-platform frozen passport serialization regression."""
import json
import unittest
from pathlib import Path, PureWindowsPath

ROOT = Path(__file__).resolve().parents[1]


class PortablePassportsTest(unittest.TestCase):
    def test_frozen_source_paths_use_forward_slashes(self):
        passports = json.loads((ROOT / "results/corpus/passports.json").read_text(encoding="utf-8"))
        for passport in passports:
            source = passport["source"]
            self.assertNotIn("\\", source, source)
            self.assertTrue(source.startswith(("sources/variants/", "sources/original/modern/")), source)

    def test_windows_relative_paths_have_same_canonical_form(self):
        path = PureWindowsPath(r"sources\variants\biblical\genesis_verses.json")
        self.assertEqual(path.as_posix(), "sources/variants/biblical/genesis_verses.json")

    def test_preparation_code_serializes_portable_paths(self):
        source = (ROOT / "src/prepare.py").read_text(encoding="utf-8")
        self.assertIn("source.relative_to(ROOT).as_posix()", source)
        self.assertIn("raw.relative_to(ROOT).as_posix()", source)
        self.assertNotIn("str(source.relative_to(ROOT))", source)
        self.assertNotIn("str(raw.relative_to(ROOT))", source)


if __name__ == "__main__":
    unittest.main()
