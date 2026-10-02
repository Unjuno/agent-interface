from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from audit import audit, exact_mcnemar_one_sided
from trials import make_trials


def evidence(root: Path, sensitive_screenshot_misses: int = 30, stable_misses: int = 0) -> None:
    rows = make_trials()
    events = []
    screen_misses = {f"b{n:02d}-sensitive-screenshot" for n in range(1, sensitive_screenshot_misses+1)}
    stable_miss_ids = {f"b{n:02d}-stable-{arm.lower()}"
                       for n in range(1, stable_misses+1) for arm in ("MINIMAL", "SCREENSHOT", "SHAM")}
    for n, row in enumerate(rows, 1):
        tid = row["trial_id"]
        start = n*1_000_000_000
        events.append({"kind":"trial_start", "trial_id":tid, "mono_ns":start, "start_ns":start,
                       "block":row["block"], "schedule":row["schedule"], "arm":row["arm"]})
        armed = start+1000
        events.append({"kind":"action_schedule", "trial_id":tid, "scheduled_ns":armed,
                       "delay_ms":row["action_delay_ms"], "arm_delay_ns":1000})
        events.append({"kind":"action_effect", "trial_id":tid, "mono_ns":start+90_000_000,
                       "action":"button.invoke", "effect_path":f"effect-{tid}.json",
                       "action_ns":armed+90_000_000, "persisted_ns":armed+90_000_100,
                       "scheduled_ns":armed})
        success = tid not in screen_misses and tid not in stable_miss_ids
        if success:
            payload = {"trial_id":tid, "value":row["expected_value"]}
            (root/f"effect-{tid}.json").write_text(json.dumps(payload))
        else:
            payload = None
        deadline = {"trial_id":tid, "deadline_ns":start+row["deadline_ms"]*1_000_000,
                    "snapshot_ns":start+row["deadline_ms"]*1_000_000+1000,
                    "effect_present":success, "effect_payload":payload}
        (root/f"deadline-{tid}.json").write_text(json.dumps(deadline))
        events.append({"kind":"deadline_observed", "mono_ns":deadline["snapshot_ns"], **deadline})
        if row["arm"] == "SCREENSHOT":
            events.append({"kind":"screenshot", "trial_id":tid, "mono_ns":start+10_000_000,
                           "request_ns":start+1, "complete_ns":start+2, "exit_code":0, "bytes":1000})
        if row["arm"] == "SHAM":
            events.append({"kind":"sham", "trial_id":tid, "mono_ns":start+10_000_000,
                           "request_ns":start+1, "complete_ns":start+2})
    (root/"app-events.jsonl").write_text("".join(json.dumps(row)+"\n" for row in events))
    (root/"candidate-receipt.json").write_text(json.dumps({"exit_code":0,"trial_count":len(rows)}))


class AuditTests(unittest.TestCase):
    def test_exact_mcnemar_direction_and_ties(self):
        self.assertEqual(exact_mcnemar_one_sided([True]*30, [False]*30), 2**-30)
        self.assertEqual(exact_mcnemar_one_sided([False]*30, [False]*30), 1.0)

    def test_scoped_positive_requires_large_paired_difference(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence(root)
            result = audit(root, make_trials())
            self.assertEqual(result["decision"], "H_PASS_SCOPED")
            self.assertEqual(result["trial_count"], 180)
            self.assertAlmostEqual(result["sensitive_miss_rate_delta_screenshot_minus_sham"], 1.0)

    def test_small_difference_does_not_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence(root, sensitive_screenshot_misses=3)
            self.assertEqual(audit(root, make_trials())["decision"], "H_FAIL_SCOPED")

    def test_unstable_negative_control_is_hold(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence(root, stable_misses=2)
            self.assertEqual(audit(root, make_trials())["decision"], "HOLD_STABLE_CONTROL_GATE")

    def test_missing_action_mutation_stops(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence(root)
            rows = (root/"app-events.jsonl").read_text().splitlines()
            (root/"app-events.jsonl").write_text("\n".join(x for x in rows if '"action_effect"' not in x)+"\n")
            result = audit(root, make_trials())
            self.assertEqual(result["decision"], "STOP_AUDIT_ERRORS")
            self.assertIn("action-count-not-exactly-one", result["errors"])

    def test_missing_screenshot_mutation_stops(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence(root)
            rows = (root/"app-events.jsonl").read_text().splitlines()
            (root/"app-events.jsonl").write_text("\n".join(x for x in rows if '"kind": "screenshot"' not in x)+"\n")
            result = audit(root, make_trials())
            self.assertEqual(result["decision"], "STOP_AUDIT_ERRORS")
            self.assertTrue(any(x.startswith("no-screenshot:") for x in result["errors"]))

    def test_formal_audit_refuses_underfilled_allocation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rows = make_trials(blocks=1)
            evidence(root)
            result = audit(root, rows)
            self.assertEqual(result["decision"], "STOP_AUDIT_ERRORS")
            self.assertIn("allocation-not-balanced", result["errors"])

    def test_duplicate_start_and_execution_reorder_stop(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence(root)
            lines = (root/"app-events.jsonl").read_text().splitlines()
            starts = [json.loads(line) for line in lines if '"kind": "trial_start"' in line]
            lines = [line for line in lines if '"kind": "trial_start"' not in line]
            lines.extend([json.dumps(starts[1]), json.dumps(starts[0]), json.dumps(starts[0])])
            (root/"app-events.jsonl").write_text("\n".join(lines)+"\n")
            result = audit(root, make_trials())
            self.assertEqual(result["decision"], "STOP_AUDIT_ERRORS")
            self.assertIn("trial-start-set-mismatch", result["errors"])
            self.assertIn("execution-order-mismatch", result["errors"])

    def test_late_callback_is_scored_as_effect_outcome_not_timing_integrity_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence(root)
            lines = (root/"app-events.jsonl").read_text().splitlines()
            changed = []
            for line in lines:
                event = json.loads(line)
                if event["kind"] == "action_effect" and event["trial_id"] == "b01-sensitive-minimal":
                    event["action_ns"] = event["scheduled_ns"] + 150_000_000
                    event["persisted_ns"] = event["action_ns"] + 100_000
                if event["kind"] == "deadline_observed" and event["trial_id"] == "b01-sensitive-minimal":
                    event["effect_present"] = False
                    event["effect_payload"] = None
                changed.append(json.dumps(event))
            (root/"app-events.jsonl").write_text("\n".join(changed)+"\n")
            raw_path = root/"deadline-b01-sensitive-minimal.json"
            raw = json.loads(raw_path.read_text())
            raw["effect_present"] = False
            raw["effect_payload"] = None
            raw_path.write_text(json.dumps(raw))
            (root/"effect-b01-sensitive-minimal.json").unlink()
            result = audit(root, make_trials())
            self.assertEqual(result["decision"], "H_PASS_SCOPED")
            self.assertEqual(result["action_after_deadline_count"], 1)

    def test_action_schedule_shift_beyond_start_bound_stops(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence(root)
            lines = (root/"app-events.jsonl").read_text().splitlines()
            changed = []
            for line in lines:
                event = json.loads(line)
                if event["kind"] == "action_schedule" and event["trial_id"] == "b01-sensitive-minimal":
                    event["arm_delay_ns"] += 6_000_000
                    event["scheduled_ns"] += 6_000_000
                changed.append(json.dumps(event))
            (root/"app-events.jsonl").write_text("\n".join(changed)+"\n")
            result = audit(root, make_trials())
            self.assertEqual(result["decision"], "STOP_AUDIT_ERRORS")
            self.assertIn("action-scheduling-integrity:b01-sensitive-minimal", result["errors"])

    def test_deadline_event_oracle_disagreement_stops(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence(root)
            lines = (root/"app-events.jsonl").read_text().splitlines()
            changed = []
            for line in lines:
                event = json.loads(line)
                if event["kind"] == "deadline_observed" and event["trial_id"] == "b01-sensitive-minimal":
                    event["effect_present"] = False
                changed.append(json.dumps(event))
            (root/"app-events.jsonl").write_text("\n".join(changed)+"\n")
            result = audit(root, make_trials())
            self.assertEqual(result["decision"], "STOP_AUDIT_ERRORS")
            self.assertIn("deadline-event-mismatch:b01-sensitive-minimal", result["errors"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
