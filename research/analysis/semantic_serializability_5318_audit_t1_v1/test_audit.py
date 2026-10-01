import json
import unittest

import audit


def base_row():
    tx = {"id": "p1", "kind": "conditional_set", "key": "x", "value": 7,
          "delta": None, "guard": "left-zero", "reads": ["x"], "writes": ["x"],
          "quality": "EXACT", "commute_rule": None, "delay": 0, "effect": "REVERSIBLE"}
    return {"scenario": "unknown_overlap", "policy": "SEMANTIC_SERIALIZABILITY",
            "initial": {"x": 0}, "transactions": [tx, dict(tx, id="p2")],
            "decision": "SERIALIZE", "final": {"x": 7}, "committed": ["p1", "p2"],
            "legal_serial_finals": [{"x": 7}, {"x": 7}], "parallel_count": 0,
            "delayed_effects": [], "irreversible_sources": []}


class IndependentAuditTests(unittest.TestCase):
    def test_left_zero_guard_reconstructs_legal_serial_outputs(self):
        row = base_row()
        reconstructed = audit.oracle(row, row["policy"])[3]
        self.assertEqual(reconstructed, [{"x": 7}, {"x": 7}])

    def test_left_zero_disagreement_is_reported(self):
        row = base_row()
        row["final"] = {"x": 0}
        errors = audit.audit_rows([row])
        self.assertIn("ROW_RECONSTRUCTION:('unknown_overlap', 'SEMANTIC_SERIALIZABILITY')", errors)

    def test_raw_coverage_rejects_duplicate_and_missing_policy_rows(self):
        rows = [base_row(), base_row()]
        self.assertIn("ROW_COVERAGE", audit.audit_rows(rows))

    def test_malformed_json_line_is_reported_not_silently_dropped(self):
        errors = audit.audit_bytes(b'{"valid":true}\nnot-json\n')
        self.assertIn("MALFORMED_JSON:2", errors[0])

    def test_raw_digest_is_of_exact_bytes(self):
        payload = b'{"x": 1}\n'
        self.assertEqual(audit.audit_bytes(payload, require_coverage=False)[1],
                         "936353965b4ba9180e3acb781d81aa634390ac95fd2874a9cbc4c4846b49fbd4")


if __name__ == "__main__":
    unittest.main()
