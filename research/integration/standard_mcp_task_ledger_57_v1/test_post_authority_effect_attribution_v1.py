"""Check whether the standard task ledger distinguishes late effects."""
import hashlib
import json
import unittest

from effect_attribution_v1 import adjudicate_effect
from ledger import summarize


# Frozen from win32_native_queue_effect_boundary_20261113/EVIDENCE.json, R149.
R149 = {
    "expiry_ns": 262847357442000,
    "release_received_ns": 262847380075400,
    "horizon_end_ns": 262849380883600,
    "recovered_terminal_observed_ns": 262849399688300,
    "effect_ns": 262850072367700,
    "effect_after_expiry_ns": 2714925700,
    "effect_after_horizon_ns": 691484100,
    "public_status": "recovered",
    "release_confirmed": True,
    "public_task_success": None,
    "replay_allowed": False,
    "task_counter": 1,
}


def state_digest(counter):
    payload = json.dumps({"task_counter": counter}, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def ledger_record(*, effect_ns, phase):
    terminal_ns = R149["recovered_terminal_observed_ns"]
    return [
        {
            "seq": 1,
            "kind": "tool_call",
            "call_id": "r149-recovered-call",
            "model_attempt_id": None,
            "method": "interface_guarded_compiled",
            "started_ns": R149["expiry_ns"] - 1_000_000,
            "ended_ns": terminal_ns,
            "result": {
                "status": R149["public_status"],
                "release_confirmed": R149["release_confirmed"],
                "task_success": R149["public_task_success"],
                "replay_allowed": R149["replay_allowed"],
            },
        },
        {
            "seq": 2,
            "kind": "task_score",
            "scorer_id": "fixture-task-counter-v1",
            "independent": True,
            "task_success": True,
            "state_sha256": state_digest(R149["task_counter"]),
            "started_ns": effect_ns,
            "ended_ns": effect_ns,
            # Current summarize() ignores this timing attribution field.
            "effect_phase": phase,
        },
    ]


class PostAuthorityEffectAttributionTests(unittest.TestCase):
    def test_existing_summary_conflates_r149_late_effect_with_timely_success(self):
        timely_events = ledger_record(effect_ns=R149["expiry_ns"] - 100,
                                      phase="within_authority")
        delayed_events = ledger_record(effect_ns=R149["effect_ns"],
                                       phase="after_release_horizon")
        timely = summarize(timely_events)
        delayed = summarize(delayed_events)

        self.assertEqual(R149["effect_after_expiry_ns"],
                         R149["effect_ns"] - R149["expiry_ns"])
        self.assertEqual(R149["effect_after_horizon_ns"],
                         R149["effect_ns"] - R149["horizon_end_ns"])
        self.assertTrue(R149["release_confirmed"])
        self.assertIsNone(R149["public_task_success"])
        self.assertFalse(R149["replay_allowed"])
        self.assertEqual(timely, delayed)
        self.assertTrue(delayed["task_success"])
        self.assertEqual(delayed["independent_score_status"], "recorded")
        self.assertNotIn("effect_phase", delayed)

    def test_r149_effect_is_factual_but_not_authority_eligible_success(self):
        result = adjudicate_effect(
            task_success=True,
            effect_observed_ns=R149["effect_ns"],
            authority_expiry_ns=R149["expiry_ns"],
            release_received_ns=R149["release_received_ns"],
            horizon_end_ns=R149["horizon_end_ns"],
        )
        self.assertEqual(result, {
            "factual_task_success": True,
            "effect_timing": "after_release_horizon",
            "eligible_task_success": False,
        })

    def test_in_authority_effect_is_eligible_and_unknown_time_stays_unknown(self):
        timely = adjudicate_effect(
            task_success=True,
            effect_observed_ns=R149["expiry_ns"],
            authority_expiry_ns=R149["expiry_ns"],
            release_received_ns=R149["release_received_ns"],
            horizon_end_ns=R149["horizon_end_ns"],
        )
        unknown = adjudicate_effect(
            task_success=True, effect_observed_ns=None,
            authority_expiry_ns=R149["expiry_ns"],
            release_received_ns=R149["release_received_ns"],
            horizon_end_ns=R149["horizon_end_ns"],
        )
        self.assertTrue(timely["eligible_task_success"])
        self.assertEqual(timely["effect_timing"], "within_authority")
        self.assertIsNone(unknown["eligible_task_success"])
        self.assertEqual(unknown["effect_timing"], "unknown")

    def test_all_expiry_release_and_horizon_time_bands_are_distinct(self):
        cases = (
            (R149["expiry_ns"], "within_authority"),
            (R149["expiry_ns"] + 1, "after_authority_before_release"),
            (R149["release_received_ns"] + 1,
             "after_release_within_horizon"),
            (R149["horizon_end_ns"] + 1, "after_release_horizon"),
        )
        for effect_ns, expected in cases:
            with self.subTest(effect_ns=effect_ns):
                result = adjudicate_effect(
                    task_success=True, effect_observed_ns=effect_ns,
                    authority_expiry_ns=R149["expiry_ns"],
                    release_received_ns=R149["release_received_ns"],
                    horizon_end_ns=R149["horizon_end_ns"],
                )
                self.assertEqual(result["effect_timing"], expected)
                self.assertEqual(result["eligible_task_success"],
                                 expected == "within_authority")

    def test_invalid_or_reordered_clock_bounds_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "expiry <= release <= horizon"):
            adjudicate_effect(task_success=True, effect_observed_ns=1,
                authority_expiry_ns=3, release_received_ns=2, horizon_end_ns=4)
        with self.assertRaisesRegex(ValueError, "nonnegative integers"):
            adjudicate_effect(task_success=True, effect_observed_ns=1,
                authority_expiry_ns=True, release_received_ns=2, horizon_end_ns=3)

    def test_recovery_result_remains_unchanged_when_late_score_is_adjudicated(self):
        events = ledger_record(effect_ns=R149["effect_ns"],
                               phase="after_release_horizon")
        public_result = events[0]["result"]
        summary = summarize(events)
        adjudicated = adjudicate_effect(
            task_success=summary["task_success"],
            effect_observed_ns=R149["effect_ns"],
            authority_expiry_ns=R149["expiry_ns"],
            release_received_ns=R149["release_received_ns"],
            horizon_end_ns=R149["horizon_end_ns"],
        )

        self.assertEqual(public_result["status"], "recovered")
        self.assertTrue(public_result["release_confirmed"])
        self.assertIsNone(public_result["task_success"])
        self.assertFalse(public_result["replay_allowed"])
        self.assertTrue(summary["task_success"])
        self.assertFalse(adjudicated["eligible_task_success"])


if __name__ == "__main__":
    unittest.main()
