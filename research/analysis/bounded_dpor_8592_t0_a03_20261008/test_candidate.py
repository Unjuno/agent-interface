"""Construction tests for the bounded DPOR schedule explorer."""

from __future__ import annotations

import unittest
import json
from pathlib import Path

from candidate import apply_event, derive_independent_pairs, initial_state, reduced_schedules, run


class ReducedScheduleTests(unittest.TestCase):
    def test_all_independent_events_have_one_sleep_set_representative(self):
        events = ("a", "b", "c", "d")
        independent = {frozenset(pair) for pair in (("a", "b"), ("a", "c"), ("a", "d"), ("b", "c"), ("b", "d"), ("c", "d"))}

        schedules, stats = reduced_schedules(events, independent)

        self.assertEqual(schedules, (("a", "b", "c", "d"),))
        self.assertEqual(stats["terminal_schedules"], 1)
        self.assertGreater(stats["sleep_pruned_prefixes"], 0)

    def test_dependent_events_retain_both_orders_and_each_fault_witness(self):
        events = ("dispatch", "revoke", "release")
        independent = {frozenset(("revoke", "release"))}

        schedules, stats = reduced_schedules(events, independent)

        self.assertEqual(len(schedules), 4)
        self.assertIn(("revoke", "dispatch", "release"), schedules)
        self.assertIn(("dispatch", "release", "revoke"), schedules)
        self.assertEqual(stats["terminal_schedules"], 4)

    def test_unknown_or_underdeclared_pair_is_not_silently_assumed_independent(self):
        events = ("receipt", "ack")

        schedules, stats = reduced_schedules(events, set())

        self.assertEqual(set(schedules), {("receipt", "ack"), ("ack", "receipt")})
        self.assertEqual(stats["terminal_schedules"], 2)


class LifecycleTransitionTests(unittest.TestCase):
    def test_stale_observation_blocks_dispatch_and_release(self):
        state = initial_state()
        state, _ = apply_event(state, {"id": "observe", "kind": "observation_update"})
        state, dispatched = apply_event(state, {"id": "dispatch", "kind": "dispatch"})
        state, released = apply_event(state, {"id": "release", "kind": "release"})

        self.assertEqual(dispatched["status"], "blocked_stale_generation")
        self.assertEqual(released["status"], "blocked_no_dispatch")
        self.assertFalse(state["physical_release"])

    def test_revocation_and_cancellation_each_block_dispatch(self):
        for event in (
            {"id": "revoke", "kind": "lease_revoke"},
            {"id": "cancel", "kind": "cancel"},
        ):
            with self.subTest(event=event["kind"]):
                state = initial_state()
                state, _ = apply_event(state, event)
                state, output = apply_event(state, {"id": "dispatch", "kind": "dispatch"})
                self.assertEqual(output["status"], "blocked_authority_or_cancel")
                self.assertFalse(state["dispatch_accepted"])

    def test_ack_before_receipt_is_retained_as_a_safety_violation(self):
        state = initial_state()
        state, ack = apply_event(state, {"id": "ack", "kind": "acknowledgement"})
        state, _ = apply_event(state, {"id": "release", "kind": "release"})
        state, _ = apply_event(state, {"id": "receipt", "kind": "effect_receipt"})

        self.assertEqual(ack["status"], "violation_ack_without_receipt")
        self.assertIn("ACK_BEFORE_EFFECT_RECEIPT", state["violations"])

    def test_disjoint_diagnostic_markers_commute_and_are_both_retained(self):
        state = initial_state()
        state, _ = apply_event(state, {"id": "diag:left", "kind": "diagnostic_marker"})
        state, _ = apply_event(state, {"id": "diag:right", "kind": "diagnostic_marker"})

        self.assertEqual(state["diagnostic_markers"], ["diag:left", "diag:right"])

    def test_unknown_dependency_metadata_defaults_to_dependent(self):
        events = (
            {"id": "known", "reads": [], "writes": ["x"]},
            {"id": "unknown", "reads": [], "writes": [], "unknown_dependency": True},
        )

        self.assertEqual(derive_independent_pairs(events), set())

    def test_independence_requires_disjoint_guard_and_effect_resources(self):
        events = (
            {"id": "observe", "reads": [], "writes": ["generation"], "guards": [], "enables": [], "effects": [], "authority_epoch": []},
            {"id": "dispatch", "reads": [], "writes": ["dispatch"], "guards": ["generation"], "enables": [], "effects": ["authority_epoch"], "authority_epoch": []},
            {"id": "note", "reads": [], "writes": ["note"], "guards": [], "enables": [], "effects": ["authority_epoch"], "authority_epoch": []},
        )

        independent = derive_independent_pairs(events)

        self.assertNotIn(frozenset(("observe", "dispatch")), independent)
        self.assertIn(frozenset(("observe", "note")), independent)
        self.assertNotIn(frozenset(("dispatch", "note")), independent)


class FrozenInputCandidateTests(unittest.TestCase):
    def test_candidate_reports_reduced_replayable_schedules_per_frozen_case(self):
        path = Path(__file__).with_name("input.json")
        data = json.loads(path.read_text(encoding="utf-8"))

        raw = run(data)

        self.assertIn("cases", raw)
        by_id = {case["case_id"]: case for case in raw["cases"]}
        self.assertEqual(set(by_id), {"lifecycle_order_faults", "commuting_heavy_diagnostics"})
        self.assertEqual(by_id["lifecycle_order_faults"]["full_schedule_count"], 5040)
        self.assertLess(by_id["lifecycle_order_faults"]["reduced_schedule_count"], 5040)
        self.assertEqual(by_id["commuting_heavy_diagnostics"]["full_schedule_count"], 40320)
        self.assertEqual(by_id["commuting_heavy_diagnostics"]["reduced_schedule_count"], 1)
        self.assertEqual(by_id["lifecycle_order_faults"]["ordered_pair_baseline"]["trace_count"], 42)
        self.assertEqual(by_id["commuting_heavy_diagnostics"]["ordered_pair_baseline"]["trace_count"], 56)
        self.assertTrue(all(case["schedule_traces"] for case in raw["cases"]))


if __name__ == "__main__":
    unittest.main()
