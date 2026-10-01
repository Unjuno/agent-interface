"""Construction and copied-raw corruption controls for the T5 oracle."""

import copy
import json
import unittest
from pathlib import Path

from audit_raw import audit


RAW = Path(__file__).with_name("raw-output.json")


class RawAuditTests(unittest.TestCase):
    def setUp(self):
        self.raw = json.loads(RAW.read_text(encoding="utf-8"))

    def test_frozen_raw_passes(self):
        self.assertEqual([], audit(self.raw))

    def test_each_matrix_row_corruption_is_rejected(self):
        for index in range(9):
            mutated = copy.deepcopy(self.raw)
            mutated["semantic"]["matrix"][index]["false_failed"] += 1
            with self.subTest(row=index):
                self.assertTrue(audit(mutated))

    def test_docker_disclosure_corruption_is_rejected(self):
        mutated = copy.deepcopy(self.raw)
        mutated["environment"]["docker_used"] = True
        self.assertTrue(audit(mutated))


if __name__ == "__main__":
    unittest.main()
