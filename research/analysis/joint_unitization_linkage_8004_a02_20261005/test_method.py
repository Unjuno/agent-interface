import copy
import inspect
import json
from pathlib import Path
import unittest

from auditor import audit
from candidate import evaluate

ROOT = Path(__file__).parent
OBS = json.loads((ROOT / "observations.json").read_text())
ORACLE = json.loads((ROOT / "oracle.json").read_text())


class IndependentOracleTests(unittest.TestCase):
    def setUp(self):
        self.candidate = evaluate(copy.deepcopy(OBS))

    def test_candidate_has_no_oracle_parameter_or_truth_payload(self):
        self.assertEqual(list(inspect.signature(evaluate).parameters), ["observations"])
        self.assertFalse(any(k in json.dumps(OBS).lower() for k in ("record_truth", "opportunity_id", "oracle")))

    def test_independent_audit_reconstructs_all_assignments_and_six_opportunities(self):
        report = audit(OBS, ORACLE, self.candidate)
        self.assertTrue(report["ok"], report["errors"])
        self.assertEqual(report["assignment_count_reconstructed"], 4)
        self.assertEqual(report["latent_opportunity_denominator"], 6)
        self.assertEqual(report["oracle_all_channel_zero_count"], 1)
        self.assertEqual(report["availability_status_counts"]["right_censored_before_opportunity"], 1)
        self.assertEqual(report["availability_status_counts"]["missing_interval"], 1)
        self.assertEqual(report["false_links_by_assignment"]["S_split+L_crossed"], 2)
        self.assertEqual(self.candidate["disposition"], "UNIDENTIFIED")

    def test_forced_consensus_segmentation_is_detected(self):
        mutated = copy.deepcopy(self.candidate)
        mutated["assignments"] = [r for r in mutated["assignments"] if not r["assignment"].startswith("S_merge+")]
        mutated["assignment_count"] = len(mutated["assignments"])
        self.assertIn("assignment_space_denominator", audit(OBS, ORACLE, mutated)["errors"])

    def test_deleted_plausible_link_is_measured_as_missed_opportunity(self):
        changed = copy.deepcopy(OBS)
        changed["linkage_alternatives"]["L_temporal"].remove(["r-01", "w-01"])
        output = evaluate(changed)
        report = audit(changed, ORACLE, output)
        self.assertTrue(report["ok"], report["errors"])
        self.assertGreater(report["missed_multichannel_opportunities_by_assignment"]["S_split+L_temporal"], 0)

    def test_false_split_or_duplicate_raw_record_is_detected(self):
        mutated = copy.deepcopy(self.candidate)
        mutated["assignments"][0]["components"][0]["records"].append("r-01")
        self.assertIn("raw_record_conservation", audit(OBS, ORACLE, mutated)["errors"])

    def test_dropped_censored_opportunity_is_detected(self):
        changed = copy.deepcopy(ORACLE)
        changed["opportunities"] = [o for o in changed["opportunities"] if o["opportunity_id"] != "F5"]
        self.assertIn("latent_opportunity_denominator", audit(OBS, changed, self.candidate)["errors"])

    def test_oracle_leak_and_zero_unseen_claim_are_rejected(self):
        leaked = copy.deepcopy(OBS)
        leaked["raw_records"][0]["truth_id"] = "F1"
        self.assertIn("oracle_leak_in_candidate_input", audit(leaked, ORACLE, evaluate(leaked))["errors"])
        mutated = copy.deepcopy(self.candidate)
        mutated["unseen_event_count"] = 0
        self.assertIn("unsupported_unseen_count", audit(OBS, ORACLE, mutated)["errors"])

    def test_wrong_unidentified_label_is_rejected(self):
        mutated = copy.deepcopy(self.candidate)
        mutated["disposition"] = "STABLE_WITHIN_AUTHORED_SET"
        self.assertIn("unidentified_label", audit(OBS, ORACLE, mutated)["errors"])


if __name__ == "__main__":
    unittest.main()
