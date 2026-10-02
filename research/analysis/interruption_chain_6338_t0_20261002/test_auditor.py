import copy
import unittest
from auditor import audit
from candidate import POLICIES, run_policy
from cases import CASES


def artifact_for(cases):
    rows = []
    for case in cases["cases"]:
        for policy in POLICIES:
            rows.append({"case_id": case["id"], **run_policy(copy.deepcopy(case), policy)})
    # The disposition is an independently audited warning, not a benefit label.
    for row in rows:
        if row["case_id"] == "opaque_negative_control" and row["policy"] == "opaque_consolidation":
            row["disposition"] = "CHAIN_REDUCTION_WITH_BURDEN_UNKNOWN_OR_WORSE"
    return {"results": rows}


class AuditorConstructionTests(unittest.TestCase):
    def test_clean_artifact_passes_scoped_audit(self):
        self.assertEqual(audit(CASES, artifact_for(CASES))["status"], "PASS_METHOD_SCOPED")

    def test_missing_parent_is_rejected(self):
        bad = copy.deepcopy(CASES)
        next(c for c in bad["cases"] if c["id"] == "two_generation_chain")["events"][1]["parent"] = "absent"
        self.assertIn("missing raw parent", " ".join(audit(bad, artifact_for(CASES))["errors"]))

    def test_cross_card_approval_mutation_is_rejected(self):
        bad = artifact_for(CASES)
        row = next(r for r in bad["results"] if r["case_id"] == "target_revision" and r["policy"] == "emit_each")
        row["approval_accepted"]["r2"] = True
        self.assertIn("stale target approval was accepted", " ".join(audit(CASES, bad)["errors"]))

    def test_suppressed_hard_alert_is_rejected(self):
        bad = artifact_for(CASES)
        row = next(r for r in bad["results"] if r["case_id"] == "urgent_hard_alert" and r["policy"] == "source_linked")
        row["cards"] = [c for c in row["cards"] if c["id"] != "card:h1"]
        row["notice_count"] -= 1
        row["hard_alert_count"] -= 1
        self.assertIn("mandatory hard alert", " ".join(audit(CASES, bad)["errors"]))

    def test_cross_principal_card_merge_is_rejected(self):
        bad = artifact_for(CASES)
        row = next(r for r in bad["results"] if r["case_id"] == "cross_principal_attempt" and r["policy"] == "source_linked")
        row["event_card"]["p1"] = row["event_card"]["p0"]
        self.assertIn("event-to-card map mismatch", " ".join(audit(CASES, bad)["errors"]))

    def test_opaque_lower_count_is_not_called_benefit(self):
        bad = artifact_for(CASES)
        row = next(r for r in bad["results"] if r["case_id"] == "opaque_negative_control" and r["policy"] == "opaque_consolidation")
        row["disposition"] = "BENEFIT"
        self.assertIn("promoted as benefit", " ".join(audit(CASES, bad)["errors"]))

    def test_parent_edge_count_is_reconstructed(self):
        bad = artifact_for(CASES)
        row = next(r for r in bad["results"] if r["case_id"] == "two_generation_chain" and r["policy"] == "emit_each")
        row["event_parent_edges"] = 0
        self.assertIn("raw parent-edge count", " ".join(audit(CASES, bad)["errors"]))

    def test_effect_count_is_independently_scored(self):
        bad = artifact_for(CASES)
        row = next(r for r in bad["results"] if r["case_id"] == "two_generation_chain" and r["policy"] == "source_linked")
        row["correct_effects"] = 2
        self.assertIn("task-effect count", " ".join(audit(CASES, bad)["errors"]))


if __name__ == "__main__":
    unittest.main()
