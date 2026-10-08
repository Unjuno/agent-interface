import copy
import json
import tempfile
import unittest
from pathlib import Path

from audit import audit_rows
from candidate import run


HERE = Path(__file__).resolve().parent


class IndependentAuditTests(unittest.TestCase):
    def setUp(self):
        self.inputs = json.loads((HERE / "inputs.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp_dir:
            raw_path = Path(temp_dir) / "raw.jsonl"
            run(HERE / "inputs.json", raw_path)
            self.rows = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines()]

    def test_pristine_candidate_rows_pass_independent_contract(self):
        self.assertEqual(audit_rows(self.inputs, self.rows), [])

    def test_corruptions_are_rejected(self):
        mutations = []

        dropped = copy.deepcopy(self.rows)
        dropped.pop()
        mutations.append(dropped)

        for field, value in (
            ("event", "owner_key_release_bracket"),
            ("owner_event", "wrong_source"),
            ("keycode", 99),
            ("grants_input_authority", True),
            ("physical_key_up_claimed", True),
            ("shared_sync_returned_ns", 1),
            ("caller_owner_id", "foreign_owner"),
        ):
            changed = copy.deepcopy(self.rows)
            changed[0][field] = value
            mutations.append(changed)

        for rows in mutations:
            with self.subTest(rows=rows):
                self.assertTrue(audit_rows(self.inputs, rows))


if __name__ == "__main__":
    unittest.main(verbosity=2)
