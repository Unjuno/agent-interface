import copy
import json
import tempfile
import unittest
from pathlib import Path

from auditor import audit, main as audit_file
from candidate import build_raw, main as write_raw


class BrokerBoundaryTests(unittest.TestCase):
    def test_full_grid_and_json_roundtrip(self):
        raw = build_raw()
        self.assertEqual(len(raw["runs"]), 18)
        self.assertEqual(audit(raw), [])
        self.assertEqual(audit(json.loads(json.dumps(raw))), [])

    def test_candidate_and_auditor_file_interfaces(self):
        with tempfile.TemporaryDirectory() as directory:
            raw_path = f"{directory}/raw.json"
            report_path = f"{directory}/audit.json"
            write_raw(raw_path)
            self.assertEqual(audit_file(raw_path, report_path), 0)
            report = json.loads(Path(report_path).read_text(encoding="utf-8"))
            self.assertEqual(report["audit"], "PASS_METHOD_SCOPED")
            self.assertEqual(report["rows"], 18)

    def test_auditor_rejects_false_baseline_contract_claim(self):
        raw = copy.deepcopy(build_raw())
        row = next(r for r in raw["runs"] if r["route"] == "heartbeat_only"
                   and r["condition"] == "stuck_pass")
        row["trace"][-1]["matches_contract"] = True
        self.assertTrue(audit(raw))

    def test_three_actual_submissions_are_rejected_at_each_boundary(self):
        for row in build_raw()["runs"]:
            attacks = row["attack_results"]
            self.assertEqual([x["attack"] for x in attacks["attempts"]], [
                "forged_capability", "old_generation_replay", "challenge_as_ordinary"])
            self.assertTrue(all(x["accepted"] is False for x in attacks["attempts"]))
            self.assertTrue(all(x["reducer_accepted"] is False
                                and x["publisher_event"] is False
                                and x["actuator_effect"] is False
                                for x in attacks["attempts"]))
            self.assertEqual(attacks["reducer_attempts"], 1)
            self.assertEqual(attacks["ordinary_reducer_accepts"], 0)
            self.assertEqual(attacks["publisher_events"], 0)
            self.assertEqual(attacks["obligation_satisfied"], 0)
            self.assertEqual(attacks["actuator_effects"], 0)

    def test_in_path_detects_each_mutant_before_release(self):
        rows = {r["condition"]: r for r in build_raw()["runs"]
                if r["route"] == "in_path_challenge"}
        for condition in ("stuck_pass", "stale_cache", "parser_omission", "skip_mandatory"):
            self.assertTrue(rows[condition]["detected_before_release"], condition)
            self.assertFalse(rows[condition]["ordinary_verdict_released"], condition)
        for condition in ("healthy", "healthy_slow"):
            self.assertFalse(rows[condition]["detected_before_release"], condition)
            self.assertTrue(rows[condition]["ordinary_verdict_released"], condition)
        wrong_binding = rows["healthy"]["trace"][5]
        self.assertEqual(wrong_binding["vector"]["source"], "verifier-X")
        self.assertEqual((wrong_binding["source"], wrong_binding["target"]),
                         ("verifier-A", "task-17"))
        self.assertEqual(wrong_binding["observed"], "REJECT")
        self.assertTrue(wrong_binding["matches_contract"])

    def test_baselines_expose_semantic_fault_escape(self):
        for route in ("heartbeat_only", "detached_startup_probe"):
            rows = [r for r in build_raw()["runs"] if r["route"] == route]
            self.assertTrue(all(r["ordinary_verdict_released"] for r in rows))
            self.assertTrue(all(not r["detected_before_release"] for r in rows))
            escaped = [r for r in rows if r["condition"] in
                       ("stuck_pass", "stale_cache", "parser_omission", "skip_mandatory")]
            self.assertTrue(all(r["trace"][-1]["matches_contract"] is False for r in escaped))
            self.assertTrue(all(r["trace"][-1]["result"] == "PASS" for r in escaped))

    def test_auditor_rejects_mutated_submission_decision_and_effect(self):
        mutations = (
            lambda x: x["runs"][0]["attack_results"]["attempts"][0]["submitted"].update(
                capability="fixture-capability-6179-t0c"),
            lambda x: x["runs"][0]["attack_results"]["attempts"][0].update(accepted=True),
            lambda x: x["runs"][0]["attack_results"].update(actuator_effects=1),
            lambda x: x["runs"][0]["attack_results"]["attempts"].pop(),
            lambda x: x["runs"].reverse(),
            lambda x: x["vectors"][5].update(target="task-17"),
        )
        for mutate in mutations:
            raw = copy.deepcopy(build_raw())
            mutate(raw)
            self.assertTrue(audit(raw))

    def test_auditor_rejects_detection_or_release_order_corruption(self):
        raw = copy.deepcopy(build_raw())
        row = next(r for r in raw["runs"] if r["route"] == "in_path_challenge"
                   and r["condition"] == "healthy")
        row["ordinary_verdict_released"] = False
        self.assertTrue(audit(raw))
        raw = copy.deepcopy(build_raw())
        row = next(r for r in raw["runs"] if r["route"] == "in_path_challenge"
                   and r["condition"] == "stale_cache")
        row["trace"][-1]["at_index"] = 2
        self.assertTrue(audit(raw))


if __name__ == "__main__":
    unittest.main(verbosity=2)
