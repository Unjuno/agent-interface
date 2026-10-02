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

    def run_checker(self, indexed_names, actual_names, mutate=None, sparse=False):
        with tempfile.TemporaryDirectory() as directory:
            checkout = Path(directory) / "checkout"
            root = checkout / "research" / "analysis"
            root.mkdir(parents=True)
            if sparse:
                metadata = checkout / ".git" / "info" / "sparse-checkout"
                metadata.parent.mkdir(parents=True)
                metadata.write_text("research/analysis/a/\n", encoding="utf-8")
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
            self.assertEqual(readme.read_text(encoding="utf-8"), text + "\n")
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

    def test_sparse_checkout_preserves_absent_sibling_entries(self):
        code, output = self.run_checker(["a", "b"], ["a"], sparse=True)
        self.assertEqual(code, 0)
        self.assertIn("Sparse checkout: absent sibling directories", output)

    def test_sparse_checkout_missing_retained_entry_still_fails(self):
        code, output = self.run_checker(["a"], ["a", "b"], sparse=True)
        self.assertEqual(code, 1)
        self.assertIn("Missing retained result/failure directories", output)

    def test_sparse_checkout_unsorted_entries_still_fail(self):
        code, _ = self.run_checker(["b", "a"], ["a"], sparse=True)
        self.assertEqual(code, 1)

    def test_sparse_checkout_duplicate_entries_still_fail(self):
        code, _ = self.run_checker(["a", "a", "b"], ["a"], sparse=True)
        self.assertEqual(code, 1)


class SparseCheckoutDetectionTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.parent = Path(directory.name)
        self.checkout = self.parent / "checkout"
        root = self.checkout / "research" / "analysis"
        root.mkdir(parents=True)
        patcher = patch.object(checker, "ROOT", root)
        patcher.start()
        self.addCleanup(patcher.stop)

    def write_sparse_metadata(self, git_dir):
        metadata = git_dir / "info" / "sparse-checkout"
        metadata.parent.mkdir(parents=True)
        metadata.write_text("research/analysis/\n", encoding="utf-8")

    def test_checkout_git_directory_is_detected(self):
        self.write_sparse_metadata(self.checkout / ".git")
        self.assertTrue(checker.checkout_is_sparse())

    def test_relative_gitdir_file_is_resolved_from_checkout(self):
        self.write_sparse_metadata(self.parent / "worktree-metadata")
        (self.checkout / ".git").write_text(
            "gitdir: ../worktree-metadata\n", encoding="utf-8"
        )
        self.assertTrue(checker.checkout_is_sparse())

    def test_absolute_gitdir_file_is_detected(self):
        git_dir = self.parent / "worktree-metadata"
        self.write_sparse_metadata(git_dir)
        (self.checkout / ".git").write_text(
            f"gitdir: {git_dir}\n", encoding="utf-8"
        )
        self.assertTrue(checker.checkout_is_sparse())

    def test_parent_repository_sparse_metadata_is_ignored(self):
        (self.checkout / ".git").mkdir()
        self.write_sparse_metadata(self.parent / ".git")
        self.assertFalse(checker.checkout_is_sparse())

    def test_checkout_without_git_metadata_is_not_sparse(self):
        self.assertFalse(checker.checkout_is_sparse())

    def test_full_checkout_is_not_sparse(self):
        (self.checkout / ".git").mkdir()
        self.assertFalse(checker.checkout_is_sparse())

    def test_invalid_gitdir_file_is_not_sparse(self):
        (self.checkout / ".git").write_text("invalid metadata\n", encoding="utf-8")
        self.assertFalse(checker.checkout_is_sparse())


if __name__ == "__main__":
    unittest.main()
