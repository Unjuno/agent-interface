"""Tests for fail-closed A04 post-run classification."""

import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location(
    "a04_audit_postrun", Path(__file__).with_name("audit_postrun.py")
)
AUDIT = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(AUDIT)

class PostrunClassificationTests(unittest.TestCase):
    def test_exact_frozen_worktree_hash_survives_git_text_normalization(self):
        import hashlib
        working = b"first line\r\nsecond line\n"
        committed = b"first line\nsecond line\n"
        expected = hashlib.sha256(working).hexdigest()
        self.assertTrue(AUDIT._frozen_source_matches(expected, working, committed))

    def test_cleanup_failure_and_plugin_fetch_remain_partial_unverifiable(self):
        stderr = "PermissionError: [WinError 32] .git\\FETCH_HEAD"
        fetch = "5fd93af4cd0c623e020d0cc7e9ce178b4ac1f70f of https://github.com/openai/plugins"
        self.assertEqual(AUDIT.classify_candidate(1, 0, stderr, fetch), "PARTIAL_OR_UNVERIFIABLE")

    def test_missing_cleanup_or_external_contact_is_not_promoted(self):
        fetch = "5fd93af4cd0c623e020d0cc7e9ce178b4ac1f70f of https://github.com/openai/plugins"
        self.assertEqual(AUDIT.classify_candidate(1, 0, "PermissionError WinError 32 FETCH_HEAD", fetch), "PARTIAL_OR_UNVERIFIABLE")
        self.assertEqual(AUDIT.classify_candidate(1, 0, "PermissionError WinError 32 FETCH_HEAD", ""), "UNVERIFIABLE")

    def test_nonempty_stdout_is_not_classified_as_the_retained_failure(self):
        self.assertEqual(AUDIT.classify_candidate(0, 12, "", ""), "UNVERIFIABLE")

if __name__ == "__main__":
    unittest.main(verbosity=2)
