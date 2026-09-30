"""Regression checks for generated navigation, without scientific execution."""

import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location(
    "analysis_index_checker", Path(__file__).with_name("check_index.py")
)
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


class AnalysisIndexTests(unittest.TestCase):
    def test_independent_additions_merge_without_shared_count_drift(self):
        base = [f"study_{i:03d}" for i in range(201)]
        left = checker.render_block(sorted(base + ["left_addition"]))
        right = checker.render_block(sorted(base + ["right_addition"]))
        union = sorted(checker.generated_dirs(left) | checker.generated_dirs(right))
        # Model a clean textual merge: preserve a branch's unchanged framing,
        # union the disjoint added lines, and leave all other text untouched.
        lines = left.splitlines()
        first = next(i for i, line in enumerate(lines) if line.startswith("- [`"))
        last = max(i for i, line in enumerate(lines) if line.startswith("- [`"))
        merged = "\n".join(lines[:first] + [f"- [`{n}/`]({n}/)" for n in union] + lines[last + 1:])
        self.assertEqual(len(union), 203)
        self.assertEqual(merged, checker.render_block(union))

    def run_checker(self, indexed_names, actual_names, mutate=None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in actual_names:
                path = root / name
                path.mkdir()
                (path / "REPORT.md").write_text("fixture only\n", encoding="utf-8")
            text = checker.render_block(indexed_names)
            if mutate:
                text = mutate(text)
            readme = root / "README.md"
            readme.write_text(text + "\n", encoding="utf-8")
            with patch.object(checker, "ROOT", root), patch.object(checker, "README", readme), patch("sys.argv", ["check_index.py"]), contextlib.redirect_stdout(io.StringIO()) as output:
                code = checker.main()
            return code, output.getvalue()

    def test_complete_sorted_membership_passes(self):
        code, _ = self.run_checker(["a", "b"], ["a", "b"])
        self.assertEqual(code, 0)

    def test_missing_retained_entry_still_fails(self):
        code, output = self.run_checker(["a"], ["a", "b"])
        self.assertEqual(code, 1)
        self.assertIn("Missing retained result/failure directories", output)

    def test_extra_entry_still_fails(self):
        code, output = self.run_checker(["a", "b"], ["a"])
        self.assertEqual(code, 1)
        self.assertIn("Generated entries point to missing directories", output)

    def test_unsorted_entries_still_fail(self):
        code, _ = self.run_checker(["b", "a"], ["a", "b"])
        self.assertEqual(code, 1)

    def test_duplicate_entry_still_fails(self):
        code, _ = self.run_checker(["a", "a"], ["a"])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
