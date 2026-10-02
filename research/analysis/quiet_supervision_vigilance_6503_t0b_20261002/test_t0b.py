from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from auditor import audit
from candidate import build
from scorer import score_all, score_one

ROOT = Path(__file__).resolve().parent
STIMULI = json.loads((ROOT / "stimuli.json").read_text())
TRUTH = json.loads((ROOT / "truth.json").read_text())
TRUTH_BY_ID = {}
for _event in STIMULI["events"]:
    _item = {**TRUTH["default"], **TRUTH["overrides"].get(_event["id"], {})}
    _item.setdefault("onset_ms", _event["time_ms"])
    _item.setdefault("expiry_ms", _event["time_ms"] + STIMULI["response_window_ms"])
    TRUTH_BY_ID[_event["id"]] = _item


def make_result():
    material = build(STIMULI)
    scored = score_all(material["rows"], TRUTH_BY_ID, TRUTH["scoring_vectors"])
    return material, scored, audit(STIMULI, TRUTH, material, scored)


class T0bTests(unittest.TestCase):
    def test_full_36_by_4_material_and_scripted_scoring(self):
        material, scored, result = make_result()
        self.assertEqual("PASS_METHOD_SCOPED", result["status"], result["errors"])
        self.assertEqual(144, len(material["rows"]))
        self.assertEqual(144, len(scored))
        self.assertEqual(36, result["unique_opportunities"])

    def test_missing_assigned_opportunity_rejected(self):
        material, scored, _ = make_result()
        material["rows"].pop()
        self.assertIn("assigned_opportunity_denominator_mismatch", audit(STIMULI, TRUTH, material, scored)["errors"])

    def test_nested_oracle_leak_rejected(self):
        material, scored, _ = make_result()
        material["rows"][0]["payload"]["evidence"]["oracle_truth"] = "hit"
        self.assertIn("oracle_only_field_leaked", audit(STIMULI, TRUTH, material, scored)["errors"])

    def test_candidate_output_does_not_alias_or_mutate_stimulus_input(self):
        stimuli = json.loads((ROOT / "stimuli.json").read_text())
        before = copy.deepcopy(stimuli)
        material = build(stimuli)
        material["rows"][0]["payload"]["evidence"]["nested_control"] = {"mutated": True}
        self.assertEqual(before, stimuli)

    def test_b_c_checkpoint_schemas_match(self):
        material, scored, _ = make_result()
        b_fields = [tuple(sorted(r["payload"].keys())) for r in material["rows"] if r["policy"] == "B_EVIDENCE" and r["review_visible"] and not r["hard_alert_visible"]]
        c_fields = [tuple(sorted(r["payload"].keys())) for r in material["rows"] if r["policy"] == "C_PERIODIC" and r["review_visible"] and not r["hard_alert_visible"]]
        self.assertEqual(6, len(b_fields))
        self.assertEqual(6, len(c_fields))
        self.assertEqual(b_fields, c_fields)
        row = next(r for r in material["rows"] if r["policy"] == "C_PERIODIC" and r["review_visible"] and not r["hard_alert_visible"])
        row["payload"]["hidden_truth"] = "anomaly"
        self.assertIn("oracle_only_field_leaked", audit(STIMULI, TRUTH, material, scored)["errors"])

    def test_invisible_anomaly_is_not_hit_or_miss(self):
        truth = TRUTH_BY_ID["late-03"]
        response = {"opportunity_id":"late-03","policy":"A_CONTINUOUS","response_ms":None,"reported_anomaly":False,"safe_action":None,"active_time_ms":0,"provenance":"synthetic-script"}
        self.assertEqual("unobservable_anomaly", score_one(truth, response)["signal_outcome"])

    def test_uncaptured_anomaly_is_absent_from_every_display_but_kept_in_denominator(self):
        material, scored, result = make_result()
        rows = [r for r in material["rows"] if r["opportunity_id"] == "late-03"]
        self.assertEqual(4, len(rows))
        self.assertTrue(all(not r["review_visible"] for r in rows))
        self.assertTrue(all(r["payload"] == {"source_ref": None, "evidence": None} for r in rows))
        self.assertEqual("PASS_METHOD_SCOPED", result["status"], result["errors"])
        self.assertEqual(144, len(scored))

    def test_no_response_remains_distinct_from_miss(self):
        truth = TRUTH_BY_ID["middle-03"]
        response = {"opportunity_id":"middle-03","policy":"A_CONTINUOUS","response_ms":None,"reported_anomaly":False,"safe_action":None,"active_time_ms":0,"provenance":"synthetic-script"}
        scored = score_one(truth, response)
        self.assertEqual("miss", scored["signal_outcome"])
        self.assertTrue(scored["no_response"])

    def test_scored_rows_never_claim_human_provenance(self):
        _, scored, _ = make_result()
        self.assertEqual({"synthetic-script"}, {row["response_provenance"] for row in scored})

    def test_late_correct_label_is_still_miss_and_delay_retained(self):
        truth = TRUTH_BY_ID["middle-03"]
        response = {"opportunity_id":"middle-03","policy":"A_CONTINUOUS","response_ms":21000,"reported_anomaly":True,"safe_action":"verify_effect","active_time_ms":420,"provenance":"synthetic-script"}
        scored = score_one(truth, response)
        self.assertEqual("miss", scored["signal_outcome"])
        self.assertTrue(scored["late_response"])
        self.assertEqual(6000, scored["response_delay_ms"])

    def test_false_alarm_and_prompted_stop_are_separate(self):
        _, scored, _ = make_result()
        by_key = {(r["opportunity_id"], r["policy"]):r for r in scored}
        self.assertEqual("false_alarm", by_key[("early-05","A_CONTINUOUS")]["signal_outcome"])
        self.assertEqual("prompted_hard_stop", by_key[("late-09","A_CONTINUOUS")]["signal_outcome"])

    def test_hard_stop_suppression_rejected(self):
        for policy in ("A_CONTINUOUS", "B_EVIDENCE", "C_PERIODIC", "D_HARD_ALERT"):
            material, scored, _ = make_result()
            row = next(r for r in material["rows"] if r["opportunity_id"] == "late-09" and r["policy"] == policy)
            row["hard_alert_visible"] = False
            self.assertIn("mandatory_hard_alert_suppressed_or_invented", audit(STIMULI, TRUTH, material, scored)["errors"], policy)

    def test_periodic_checkpoint_removal_rejected(self):
        material, scored, _ = make_result()
        row = next(r for r in material["rows"] if r["opportunity_id"] == "early-04" and r["policy"] == "C_PERIODIC")
        row["review_visible"] = False
        self.assertIn("fixed_schedule_deviation", audit(STIMULI, TRUTH, material, scored)["errors"])


if __name__ == "__main__":
    unittest.main()
