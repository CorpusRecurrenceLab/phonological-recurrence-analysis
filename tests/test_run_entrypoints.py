"""Check entry point relocation without executing long research calculations."""
import ast
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
ENTRY = ("project", "tanakh", "reproduce_all", "reproduce_comparisons", "verify_unified")

class EntryPointTests(unittest.TestCase):
    def test_entrypoints_are_under_run(self):
        for name in ENTRY:
            self.assertFalse((ROOT / (name + ".py")).exists())
            path = ROOT / "run" / (name + ".py")
            self.assertTrue(path.is_file(), name)
            ast.parse(path.read_text(encoding="utf-8"))

    def test_root_resolution_is_portable(self):
        for name in ENTRY:
            text = (ROOT / "run" / (name + ".py")).read_text(encoding="utf-8")
            self.assertIn("Path(__file__).resolve().parent.parent", text)

    def test_help_commands(self):
        for name in ("project", "tanakh"):
            result = subprocess.run([sys.executable, str(ROOT / "run" / (name + ".py")), "--help"], cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_batch_and_ci_reference_new_path(self):
        for path in [*ROOT.glob("run/*.bat"), ROOT / ".github/workflows/ci.yml"]:
            text = path.read_text(encoding="utf-8")
            for name in ENTRY:
                import re
                self.assertNotRegex(text, rf"(?<![\w/]){name}\.py\b", str(path))
