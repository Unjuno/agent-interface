from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from verify import normalized_equal


PACKAGE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]


class CorpusIdentityTests(unittest.TestCase):
    def test_frozen_reproduction_matches_committed_result(self):
        completed = subprocess.run(
            [sys.executable, str(PACKAGE / "reproduce.py")],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        reproduced = json.loads(completed.stdout)
        frozen = json.loads((PACKAGE / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(reproduced, frozen)

    def test_independent_verifier_passes_committed_corpus_pair(self):
        completed = subprocess.run(
            [sys.executable, str(PACKAGE / "verify.py")],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "AUDIT_PASS_CORPUS_EOLO_ONLY")
        self.assertTrue(result["actual"]["records_equal"])
        self.assertTrue(result["mutation_controls"]["single_non_eol_byte_change_rejected"])

    def test_single_non_eol_mutation_is_not_normalized_away(self):
        left = b'{"value":1}\n'
        right = b'{"value":1}\r\n'
        self.assertTrue(normalized_equal(left, right))
        mutated = b'{"value":2}\n'
        self.assertFalse(normalized_equal(mutated, right))


if __name__ == "__main__":
    unittest.main()
