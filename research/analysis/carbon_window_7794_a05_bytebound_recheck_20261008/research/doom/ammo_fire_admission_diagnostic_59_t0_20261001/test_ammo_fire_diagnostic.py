import unittest

from analyze_ammo_fire_diagnostic import analyze_events
from audit_ammo_fire_diagnostic import audit_events


def sample_events(*, include_source=True, partial=False):
    rows = []
    if include_source:
        rows.append({"event": "typed_observation", "sequence": 10,
                     "capture_ns": 100, "signals": {"ammo": {"status": "observed", "value": 5}}})
    rows.extend([
        {"event": "command", "command": {"op": "submit", "id": "fire",
         "expected_sequence": 10, "steps": [{"op": "hold", "keys": ["Down", "space"], "duration_ms": 100}]}},
        {"event": "step_started", "id": "fire", "step": 0, "operation": "hold", "issued_ns": 200},
        {"event": "input_admission", "key": "Down", "admitted_ns": 210, "input_ack_ns": 211},
    ])
    if not partial:
        rows.extend([
            {"event": "input_admission", "key": "space", "admitted_ns": 212, "input_ack_ns": 213},
            {"event": "keys_held", "id": "fire", "step": 0,
             "keys": ["Down", "space"], "input_ack_ns": 220},
            {"event": "typed_observation", "id": "fire", "step": 0,
             "sequence": 11, "capture_ns": 250,
             "signals": {"ammo": {"status": "observed", "value": 4}}},
            {"event": "observation", "id": "fire", "step": 0, "sequence": 11,
             "capture_ns": 250},
            {"event": "typed_observation", "id": "fire", "step": 0,
             "sequence": 12, "capture_ns": 290,
             "signals": {"ammo": {"status": "observed", "value": 1}}},
            {"event": "observation", "id": "fire", "step": 0, "sequence": 12,
             "capture_ns": 290},
            {"event": "step_completed", "id": "fire", "step": 0, "completed_ns": 300},
        ])
    else:
        rows.append({"event": "terminal", "id": "fire", "status": "cancelled",
                     "release": {"verified": True, "keys_down": [], "verified_ns": 230}})
    return rows


class AmmoFireDiagnosticTests(unittest.TestCase):
    def test_completed_space_hold_uses_only_in_loop_samples_and_matches_exact_keyset(self):
        result = analyze_events(sample_events())
        self.assertEqual(len(result["space_steps"]), 1)
        row = result["space_steps"][0]
        self.assertEqual(row["status"], "completed_keyset_confirmed")
        self.assertEqual(row["source_ammo"], 5)
        self.assertEqual(row["in_loop_ammo_values"], [4])
        self.assertTrue(row["ammo_decreased_in_loop"])

    def test_partial_multikey_cancellation_is_not_counted_as_confirmed_firing(self):
        result = analyze_events(sample_events(partial=True))
        self.assertEqual(len(result["space_steps"]), 1)
        row = result["space_steps"][0]
        self.assertEqual(row["status"], "partial_or_unconfirmed_no_keyset_marker")
        self.assertEqual(result["counts"]["completed_keyset_confirmed"], 0)

    def test_future_typed_ammo_cannot_be_used_as_pre_step_source(self):
        result = analyze_events(sample_events(include_source=False))
        self.assertEqual(len(result["space_steps"]), 1)
        row = result["space_steps"][0]
        self.assertIsNone(row["source_ammo"])
        self.assertEqual(row["source_status"], "no_pre_step_typed_ammo")

    def test_independent_auditor_accepts_hand_checked_fixture(self):
        events = sample_events()
        result = analyze_events(events)
        errors = audit_events(events, result)
        self.assertEqual(errors, [])

    def test_independent_auditor_rejects_falsified_ammo_decrease(self):
        events = sample_events()
        result = analyze_events(events)
        result["space_steps"][0]["ammo_decreased_in_loop"] = False
        errors = audit_events(events, result)
        self.assertTrue(any(error.startswith("space-step semantic mismatch") for error in errors))

    def test_independent_auditor_rejects_partial_step_labeled_completed(self):
        events = sample_events(partial=True)
        result = analyze_events(events)
        result["space_steps"][0]["status"] = "completed_keyset_confirmed"
        errors = audit_events(events, result)
        self.assertTrue(any(error.startswith("space-step semantic mismatch") for error in errors))


if __name__ == "__main__":
    unittest.main()
