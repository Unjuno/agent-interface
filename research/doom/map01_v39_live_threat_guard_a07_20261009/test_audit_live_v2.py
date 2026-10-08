"""Synthetic regressions for A07 post-run custody reconciliation."""
import importlib.util
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).with_name("audit_live_v2.py")
SPEC = importlib.util.spec_from_file_location("a07_audit_live_v2", SCRIPT)
AUDITOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDITOR)


EMPTY = {"verified": True, "keys_down": [], "buttons_down": [], "keys_unknown": []}
NONEMPTY = {"verified": True, "keys_down": ["W"], "buttons_down": [], "keys_unknown": []}


class AuditLiveV2Tests(unittest.TestCase):
    def run_audit(self, events=None, decisions=None, scorer=None):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = root / "episode" / "runtime"
            runtime.mkdir(parents=True)
            (root / "episode" / "report.json").write_text(json.dumps({"decisions": decisions or []}))
            (root / "AUDIT.json").write_text("{}\n")
            (runtime / "score.json").write_text("{}\n")
            (runtime / "events.jsonl").write_text("".join(json.dumps(r) + "\n" for r in (events or [])))
            (runtime / "scorer-events.jsonl").write_text("".join(json.dumps(r) + "\n" for r in (scorer or [])))
            with mock.patch.object(AUDITOR, "ROOT", root), redirect_stdout(io.StringIO()):
                result = AUDITOR.main()
            return json.loads((root / "AUDIT_V2.json").read_text()), result

    def valid_case(self, *, admitted=False, release=True, decision_time=150,
                   guard_receive=145, scorer_time=175, guard=True):
        events = [{"event": "cancel_requested", "id": "c1", "matched": True,
                   "requested_ns": 100}]
        if admitted:
            events += [
                {"event": "input_admission", "id": "c1", "key": "W",
                 "step": 0, "intent_token": "intent-1", "admitted_ns": 90},
                {"event": "input_release_transition", "id": "c1",
                 "key": "W", "step": 0, "intent_token": "intent-1",
                 "release_batch_complete": True,
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
        self.assertTrue(audit["scoped_pass"])
        self.assertFalse(audit["formal_pass"])

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

    def test_admission_after_cancel_fails_custody(self):
        events, decisions, scorer = self.valid_case(admitted=True)
        admission = next(row for row in events if row["event"] == "input_admission")
        admission["admitted_ns"] = 101
        audit, _ = self.run_audit(events, decisions, scorer)
        self.assertEqual(audit["status"], "FAIL")
        self.assertFalse(audit["checks"]["all_matched_cancellations_closed_empty"])

    def test_admission_without_timestamp_fails_custody(self):
        events, decisions, scorer = self.valid_case(admitted=True)
        admission = next(row for row in events if row["event"] == "input_admission")
        del admission["admitted_ns"]
        audit, _ = self.run_audit(events, decisions, scorer)
        self.assertEqual(audit["status"], "FAIL")

    def test_key_up_from_wrong_step_fails_custody(self):
        events, decisions, scorer = self.valid_case(admitted=True)
        transition = next(row for row in events if row["event"] == "input_release_transition")
        transition["step"] = 1
        audit, _ = self.run_audit(events, decisions, scorer)
        self.assertEqual(audit["status"], "FAIL")

    def test_key_up_from_wrong_intent_fails_custody(self):
        events, decisions, scorer = self.valid_case(admitted=True)
        transition = next(row for row in events if row["event"] == "input_release_transition")
        transition["intent_token"] = "intent-other"
        audit, _ = self.run_audit(events, decisions, scorer)
        self.assertEqual(audit["status"], "FAIL")

    def test_duplicate_admission_and_transition_identity_fails_custody(self):
        events, decisions, scorer = self.valid_case(admitted=True)
        admission = next(row for row in events if row["event"] == "input_admission")
        transition = next(row for row in events if row["event"] == "input_release_transition")
        events.extend([dict(admission), dict(transition)])
        audit, _ = self.run_audit(events, decisions, scorer)
        self.assertEqual(audit["status"], "FAIL")

    def test_unhashable_identity_fields_fail_closed_with_audit_result(self):
        for field, malformed in (("key", []), ("step", []), ("intent_token", {})):
            with self.subTest(field=field):
                events, decisions, scorer = self.valid_case(admitted=True)
                admission = next(row for row in events if row["event"] == "input_admission")
                transition = next(row for row in events if row["event"] == "input_release_transition")
                admission[field] = malformed
                transition[field] = malformed
                audit, _ = self.run_audit(events, decisions, scorer)
                self.assertEqual(audit["status"], "FAIL")
                self.assertFalse(audit["formal_pass"])
                self.assertFalse(audit["checks"]["all_matched_cancellations_closed_empty"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
