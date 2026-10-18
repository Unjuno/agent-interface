import copy
import json
import unittest
from pathlib import Path

import candidate
from audit import audit_payload


ROOT = Path(__file__).parent


def source_data():
    fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
    truth = json.loads((ROOT / "truth.json").read_text(encoding="utf-8"))
    raw = candidate.run(fixture)
    return fixture, truth, raw


class IndependentAuditTests(unittest.TestCase):
    def test_complete_constructed_packet_reconciles(self):
        fixture, truth, raw = source_data()
        report = audit_payload(fixture, truth, raw)
        self.assertEqual([], report["errors"])
        self.assertEqual(84, report["row_count"])
        self.assertEqual(8 / 14, report["base_metrics_v1"]["no_memory"]["invalid_proposal_rate"])
        self.assertEqual(5 / 14, report["base_metrics_v1"]["prose"]["invalid_proposal_rate"])
        self.assertEqual(2 / 14, report["base_metrics_v1"]["structured"]["invalid_proposal_rate"])
        self.assertEqual(4, report["changed_envelope_controls_structured_passed"])
        self.assertEqual("PASS_METHOD_SCOPED", report["disposition"])

    def test_duplicate_row_is_rejected(self):
        fixture, truth, raw = source_data()
        changed = copy.deepcopy(raw)
        changed["rows"].append(copy.deepcopy(changed["rows"][0]))
        self.assertTrue(audit_payload(fixture, truth, changed)["errors"])

    def test_missing_counterexample_is_rejected(self):
        fixture, truth, raw = source_data()
        changed = copy.deepcopy(fixture)
        changed["rejection_memory"] = changed["rejection_memory"][1:]
        self.assertTrue(audit_payload(changed, truth, raw)["errors"])

    def test_changed_envelope_corruption_is_rejected(self):
        fixture, truth, raw = source_data()
        changed = copy.deepcopy(fixture)
        changed["target_cards"][0]["versions"]["v2"]["objective"] = "exact_state"
        self.assertTrue(audit_payload(changed, truth, raw)["errors"])

    def test_change_control_relabeling_is_rejected(self):
        fixture, truth, raw = source_data()
        changed = copy.deepcopy(raw)
        row = next(x for x in changed["rows"] if x["target_version"] == "v2")
        row["target_version"] = "v1"
        self.assertTrue(audit_payload(fixture, truth, changed)["errors"])

    def test_arm_label_leak_into_scorer_context_is_rejected(self):
        fixture, truth, raw = source_data()
        changed = copy.deepcopy(raw)
        changed["rows"][0]["scorer_context_words"][0] = changed["rows"][0]["condition"]
        self.assertTrue(audit_payload(fixture, truth, changed)["errors"])


if __name__ == "__main__":
    unittest.main()
