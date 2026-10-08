import hashlib
import json
from pathlib import Path
import unittest

import runner


class ContractTests(unittest.TestCase):
    def test_exact_28_input_inventory_and_14_raw_results(self):
        paths = runner.expected_paths()
        self.assertEqual(len(paths), 28)
        self.assertEqual(len(set(paths)), 28)
        self.assertEqual(sum(path.endswith("result.json") for path in paths), 14)

    def test_candidate_copy_hash_matches_pr_freeze(self):
        package = Path(__file__).resolve().parent
        freeze = json.loads((package / "FREEZE.json").read_text(encoding="utf-8"))
        digest = hashlib.sha256((package / "freeze_inputs_candidate.py").read_bytes()).hexdigest()
        self.assertEqual(digest, freeze["candidate_copy_sha256"])


if __name__ == "__main__":
    unittest.main()
