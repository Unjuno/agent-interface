"""Synthetic regressions for A07 post-run custody reconciliation."""
import importlib.util
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).with_name("audit_live_v3.py")
SPEC = importlib.util.spec_from_file_location("a07_audit_live_v3", SCRIPT)
AUDITOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDITOR)
V2_SCRIPT = Path(__file__).with_name("audit_live_v2.py")
V2_SPEC = importlib.util.spec_from_file_location("a07_audit_live_v2_baseline", V2_SCRIPT)
AUDITOR_V2 = importlib.util.module_from_spec(V2_SPEC)
V2_SPEC.loader.exec_module(AUDITOR_V2)


EMPTY = {"verified": True, "keys_down": [], "buttons_down": [], "keys_unknown": []}
NONEMPTY = {"verified": True, "keys_down": ["W"], "buttons_down": [], "keys_unknown": []}


class AuditLiveV3Tests(unittest.TestCase):
    def run_audit(self, events=None, decisions=None, scorer=None, *, auditor=AUDITOR,
                  result_name="AUDIT_V3.json"):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = root / "episode" / "runtime"
            runtime.mkdir(parents=True)
            (root / "episode" / "report.json").write_text(json.dumps({"decisions": decisions or []}))
            (root / "AUDIT.json").write_text("{}\n")
            (root / "AUDIT_V2.json").write_text("{\"prior\":true}\n")
            (runtime / "score.json").write_text("{}\n")
            (runtime / "events.jsonl").write_text("".join(json.dumps(r) + "\n" for r in (events or [])))
            (runtime / "scorer-events.jsonl").write_text("".join(json.dumps(r) + "\n" for r in (scorer or [])))
            with mock.patch.object(auditor, "ROOT", root), redirect_stdout(io.StringIO()):
                result = auditor.main()
            return json.loads((root / result_name).read_text()), result

    def valid_case(self, *, admitted=False, release=True, decision_time=150,
                   guard_receive=145, scorer_time=175, guard=True):
        events = []
        if admitted:
            events.append({"event": "input_admission", "id": "c1", "key": "W",
                           "admitted_ns": 90})
        events.append({"event": "cancel_requested", "id": "c1", "matched": True,
                       "requested_ns": 100})
        if admitted:
            events += [
                {"event": "input_release_transition", "id": "c1",
                 "key": "W", "release_batch_complete": True,
                 "owner_thread_keyup_verified": True},
            ]
            if release:
                events.append({"event": "input_released", "id": "c1", "owner_release": EMPTY})
        events.append({"event": "terminal", "id": "c1", "release": EMPTY})
        invalidation = None
        if guard:
            invalidation = {
                "reason": "health:below_hard_minimum",
                "sequence": 9,
                "monitor_received_ns": guard_receive,
                "outcome_evaluated_ns": decision_time,
                "outcomes": {"health": {"status": "HARD_INVALIDATED", "reason": "below_hard_minimum"}},
            }
        decisions = [{
            "iteration": 0,
            "controller_model_started_ns": 100,
            "controller_model_ended_ns": 200,
            "policy_invalidation": invalidation,
        }]
        scorer = [{"useful": True, "kind": "KILL_COUNT_INCREASE", "observed_ns": scorer_time}]
        return events, decisions, scorer

    def test_duplicate_bad_terminal_cannot_be_hidden_by_later_empty_terminal(self):
        events, decisions, scorer = self.valid_case()
        events.insert(-1, {"event": "terminal", "id": "c1", "release": NONEMPTY})
        audit, _ = self.run_audit(events, decisions, scorer)
        self.assertEqual(audit["status"], "FAIL")
        self.assertFalse(audit["checks"]["all_matched_cancellations_closed_empty"])

    def test_duplicate_release_event_is_rejected(self):
        events, decisions, scorer = self.valid_case(admitted=True)
        release = next(row for row in events if row["event"] == "input_released")
        events.append(dict(release))
        audit, _ = self.run_audit(events, decisions, scorer)
        self.assertEqual(audit["status"], "FAIL")

    def test_admitted_key_without_matching_transition_fails_custody(self):
        events, decisions, scorer = self.valid_case(admitted=True)
        events[:] = [row for row in events if row["event"] != "input_release_transition"]
        audit, _ = self.run_audit(events, decisions, scorer)
        self.assertEqual(audit["status"], "FAIL")

    def test_duplicate_per_key_transition_fails_custody(self):
        events, decisions, scorer = self.valid_case(admitted=True)
        transition = next(row for row in events if row["event"] == "input_release_transition")
        events.append(dict(transition))
        audit, _ = self.run_audit(events, decisions, scorer)
        self.assertEqual(audit["status"], "FAIL")

    def test_no_admission_needs_only_one_verified_empty_terminal(self):
        audit, _ = self.run_audit(*self.valid_case())
        self.assertEqual(audit["status"], "PASS")
        self.assertTrue(audit["checks"]["all_matched_cancellations_closed_empty"])
        self.assertFalse(audit["formal_pass"])

    def test_admitted_input_with_complete_release_can_pass_scoped_reconciliation(self):
        audit, _ = self.run_audit(*self.valid_case(admitted=True))
        self.assertEqual(audit["status"], "PASS")

    def test_input_admitted_after_cancel_cannot_pass_custody(self):
        events, decisions, scorer = self.valid_case()
        events.insert(1, {"event": "input_admission", "id": "c1", "key": "W"})
        events.insert(2, {"event": "input_release_transition", "id": "c1", "key": "W",
                          "release_batch_complete": True,
                          "owner_thread_keyup_verified": True})
        events.insert(3, {"event": "input_released", "id": "c1", "owner_release": EMPTY})
        audit, _ = self.run_audit(events, decisions, scorer)
        self.assertEqual(audit["status"], "FAIL")
        row = audit["per_cancellation"][0]
        self.assertEqual(row["input_admitted_before_cancel"], 0)
        self.assertEqual(row["post_cancel_input_admission_count"], 1)
        self.assertFalse(row["admission_temporal_order_ok"])

    def test_same_counterexample_false_passes_v2_and_fails_v3(self):
        events, decisions, scorer = self.valid_case()
        events.insert(1, {"event": "input_admission", "id": "c1", "key": "W"})
        events.insert(2, {"event": "input_release_transition", "id": "c1", "key": "W",
                          "release_batch_complete": True,
                          "owner_thread_keyup_verified": True})
        events.insert(3, {"event": "input_released", "id": "c1", "owner_release": EMPTY})
        v2, _ = self.run_audit(events, decisions, scorer, auditor=AUDITOR_V2,
                               result_name="AUDIT_V2.json")
        v3, _ = self.run_audit(events, decisions, scorer)
        self.assertEqual(v2["status"], "PASS")
        self.assertEqual(v2["per_cancellation"][0]["input_admitted_before_cancel"], 1)
        self.assertEqual(v3["status"], "FAIL")
        self.assertEqual(v3["per_cancellation"][0]["post_cancel_input_admission_count"], 1)

    def test_admission_timestamp_after_cancel_fails_even_if_log_row_precedes(self):
        events, decisions, scorer = self.valid_case()
        events.insert(0, {"event": "input_admission", "id": "c1", "key": "W",
                          "admitted_ns": 101})
        events[1]["requested_ns"] = 100
        events.insert(2, {"event": "input_release_transition", "id": "c1", "key": "W",
                          "release_batch_complete": True,
                          "owner_thread_keyup_verified": True})
        events.insert(3, {"event": "input_released", "id": "c1", "owner_release": EMPTY})
        audit, _ = self.run_audit(events, decisions, scorer)
        self.assertEqual(audit["status"], "FAIL")
        self.assertFalse(audit["per_cancellation"][0]["admission_temporal_order_ok"])

    def test_delayed_admission_event_uses_pre_cancel_monotonic_timestamp(self):
        events, decisions, scorer = self.valid_case()
        events[0]["requested_ns"] = 100
        events.insert(1, {"event": "input_admission", "id": "c1", "key": "W",
                          "admitted_ns": 90})
        events.insert(2, {"event": "input_release_transition", "id": "c1", "key": "W",
                          "release_batch_complete": True,
                          "owner_thread_keyup_verified": True})
        events.insert(3, {"event": "input_released", "id": "c1", "owner_release": EMPTY})
        audit, _ = self.run_audit(events, decisions, scorer)
        self.assertEqual(audit["status"], "PASS")
        self.assertTrue(audit["per_cancellation"][0]["admission_temporal_order_ok"])
        self.assertEqual(audit["per_cancellation"][0]["input_admitted_before_cancel"], 1)

    def test_new_audit_preserves_the_v2_result_digest(self):
        audit, _ = self.run_audit(*self.valid_case())
        self.assertEqual(audit["schema"], "map01-v39-live-threat-guard-audit-v3")
        self.assertEqual(len(audit["preserves_audit_v2_sha256"]), 64)

    def test_admitted_input_without_release_fails_custody(self):
        audit, _ = self.run_audit(*self.valid_case(admitted=True, release=False))
        self.assertEqual(audit["status"], "FAIL")

    def test_out_of_window_scorer_does_not_expose_scope(self):
        audit, _ = self.run_audit(*self.valid_case(scorer_time=300))
        self.assertEqual(audit["status"], "HOLD")
        self.assertFalse(audit["checks"]["useful_feedback_during_pending_model"])

    def test_out_of_window_health_guard_does_not_expose_scope(self):
        audit, _ = self.run_audit(*self.valid_case(decision_time=250, guard_receive=245))
        self.assertEqual(audit["status"], "HOLD")
        self.assertFalse(audit["checks"]["hard_health_guard_exposed"])

    def test_guard_without_monotonic_timestamp_does_not_expose_scope(self):
        events, decisions, scorer = self.valid_case()
        del decisions[0]["policy_invalidation"]["monitor_received_ns"]
        del decisions[0]["policy_invalidation"]["outcome_evaluated_ns"]
        audit, _ = self.run_audit(events, decisions, scorer)
        self.assertEqual(audit["status"], "HOLD")
        self.assertFalse(audit["checks"]["hard_health_guard_exposed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
