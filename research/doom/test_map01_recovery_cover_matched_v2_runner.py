import copy
import unittest

import map01_recovery_cover_matched_v2_runner as r


def owner(**overrides):
    row = {
        "schema": r.EXPECTED_OWNER_SCHEMA,
        "allocation_id": r.ALLOCATION_ID,
        "workflow_path": r.EXPECTED_WORKFLOW_PATH,
        "required_branch": "main",
        "result_class": "PASS_CANONICAL_GLOBAL_OWNER",
        "may_enter_formal_step": True,
        "current_head_branch": "main",
        "owner_head_branch": "main",
        "matching_run_count": 1,
        "current_run_id": 7,
        "owner_run_id": 7,
    }
    row.update(overrides)
    return row


class RunnerTests(unittest.TestCase):
    def test_owner_pass(self):
        r.validate_launch_owner(owner())

    def test_owner_fail_closed(self):
        cases = [
            {"matching_run_count": 2},
            {"result_class": "FAIL_NOT_CANONICAL_GLOBAL_OWNER"},
            {"current_head_branch": "feature"},
            {"owner_run_id": 6},
            {"allocation_id": "old"},
            {"workflow_path": ".github/workflows/other.yml"},
        ]
        for change in cases:
            with self.subTest(change=change), self.assertRaises(ValueError):
                r.validate_launch_owner(owner(**change))

    def test_program_bounds(self):
        coast = r.build_coast_steps()
        self.assertEqual(coast, [{"op": "coast", "duration_ms": 600, "sample_ms": 50}])
        rec = r.build_recovery_steps()
        self.assertEqual(len(rec), 10)
        self.assertEqual(sum(x.get("duration_ms", 0) for x in rec), 250)
        self.assertLessEqual(sum(x.get("duration_ms", 0) for x in rec), r.RECOVERY_LEASE_MS)
        self.assertLessEqual(r.RECOVERY_LEASE_MS, 1500)

    def test_recovery_deadline_source_bounded(self):
        self.assertEqual(r.recovery_valid_until_ns(1_000_000_000, 1_100_000_000), 1_500_000_000)
        self.assertEqual(r.recovery_valid_until_ns(1_000_000_000, 1_900_000_000), 2_000_000_000)
        with self.assertRaises(ValueError):
            r.recovery_valid_until_ns(1_000_000_000, 2_000_000_000)

    def test_guard(self):
        base = {"event": "typed_observation", "sequence": 11, "signals": {"health": {"status": "observed", "value": 90}}}
        self.assertEqual(r.recovery_guard_failed(90, 10, base), (False, None))
        damaged = copy.deepcopy(base)
        damaged["signals"]["health"]["value"] = 89
        self.assertEqual(r.recovery_guard_failed(90, 10, damaged), (True, "health_loss"))
        stale = copy.deepcopy(base)
        stale["sequence"] = 10
        self.assertEqual(r.recovery_guard_failed(90, 10, stale), (True, "non_fresh_sequence"))
        unknown = copy.deepcopy(base)
        unknown["signals"]["health"]["status"] = "unknown"
        self.assertEqual(r.recovery_guard_failed(90, 10, unknown), (True, "health_unavailable"))

    def test_union_no_double_count(self):
        w = r.Window(0, 100)
        self.assertEqual(r.union_duration_ns([(10, 50), (40, 90)], w), 80)
        self.assertEqual(r.union_duration_ns([(-10, 10), (90, 120)], w), 20)

    def test_fallback_bounds_coast(self):
        events = [{"event": "accepted", "id": "f", "intent_token": "t"}]
        out = r.fallback_input_bounds(events, "f", r.Window(100, 700))
        self.assertTrue(out["valid"])
        self.assertEqual(out["retained_input_upper_bound_ns"], 0)
        self.assertEqual(out["no_retained_input_upper_bound_ns"], 600)

    def test_fallback_bounds_recovery_union(self):
        events = [
            {"event": "accepted", "id": "f", "intent_token": "t"},
            {"event": "input_admission", "key": "d", "intent_token": "t", "admitted_ns": 110, "input_ack_ns": 120},
            {"event": "input_release_transition", "operation": "up", "key": "d", "intent_token": "t", "release_call_started_ns": 200, "release_call_returned_ns": 210, "owner_transition_verified": True},
            {"event": "input_admission", "key": "d", "intent_token": "t", "admitted_ns": 190, "input_ack_ns": 195},
            {"event": "input_release_transition", "operation": "up", "key": "d", "intent_token": "t", "release_call_started_ns": 260, "release_call_returned_ns": 270, "owner_transition_verified": True},
        ]
        out = r.fallback_input_bounds(events, "f", r.Window(100, 300))
        self.assertEqual(out["retained_input_lower_bound_ns"], 140)
        self.assertEqual(out["retained_input_upper_bound_ns"], 160)
        self.assertEqual(out["no_retained_input_upper_bound_ns"], 60)

    def test_fallback_bounds_fail_unverified(self):
        events = [
            {"event": "accepted", "id": "f", "intent_token": "t"},
            {"event": "input_admission", "key": "d", "intent_token": "t", "admitted_ns": 110, "input_ack_ns": 120},
            {"event": "input_release_transition", "operation": "up", "key": "d", "intent_token": "t", "release_call_started_ns": 200, "release_call_returned_ns": 210, "owner_transition_verified": False},
        ]
        self.assertFalse(r.fallback_input_bounds(events, "f", r.Window(100, 300))["valid"])

    def test_classification_mechanism_only(self):
        def arm(name, no_input, positive=0, negative=0):
            events = [{"useful": True, "polarity": "positive"}] * positive
            events += [{"useful": False, "polarity": "negative"}] * negative
            return {
                "arm": name,
                "pair_index": 1,
                "terminal_release_verified": True,
                "input_bounds": {"valid": True, "no_retained_input_upper_bound_ns": no_input},
                "scorer_summary": {"scheduler": {"missed_sample_periods": 0}},
                "scorer_events": events,
                "score": {"kill_count": 0, "death_count": 0, "map_exit": False, "player_dead": False, "episode_finished": False},
            }
        summary = r.classify_all([arm("COAST_CONTROL", 600), arm("BOUNDED_RECOVERY", 300)])
        self.assertEqual(summary["decision"], "HOLD_MECHANISM_ONLY")

    def test_classification_fail_on_harm(self):
        def arm(name, no_input, negative=False):
            return {
                "arm": name,
                "pair_index": 1,
                "terminal_release_verified": True,
                "input_bounds": {"valid": True, "no_retained_input_upper_bound_ns": no_input},
                "scorer_summary": {"scheduler": {"missed_sample_periods": 0}},
                "scorer_events": [{"useful": False, "polarity": "negative"}] if negative else [],
                "score": {"kill_count": 0, "death_count": 0, "map_exit": False, "player_dead": False, "episode_finished": False},
            }
        summary = r.classify_all([arm("COAST_CONTROL", 600), arm("BOUNDED_RECOVERY", 300, True)])
        self.assertEqual(summary["decision"], "FAIL")


if __name__ == "__main__":
    unittest.main()
