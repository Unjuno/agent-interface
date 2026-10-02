"""Pre-freeze construction checks; these are not formal result gates."""

import hashlib
import unittest

import scenarios


class ScenarioConstructionTests(unittest.TestCase):
    def test_generation_is_byte_deterministic(self):
        self.assertEqual(scenarios.canonical_bytes(), scenarios.canonical_bytes())
        self.assertEqual(
            hashlib.sha256(scenarios.canonical_bytes()).hexdigest(),
            hashlib.sha256(scenarios.canonical_bytes()).hexdigest(),
        )

    def test_all_boundary_cuts_and_valid_cancel_windows_are_present(self):
        cases = scenarios.build_scenarios()
        self.assertEqual(set(scenarios.BOUNDARY_CUTS),
                         {case["cut"] for case in cases if case["cut"] >= 0})
        for case in cases:
            if case["resolution"] == "cancel_before_start":
                self.assertLessEqual(case["cut"], 2)
            if case["resolution"] == "cancel_before_effect":
                self.assertLessEqual(case["cut"], 3)

    def test_event_identity_order_and_fresh_coverage(self):
        for case in scenarios.build_scenarios():
            events = case["events"]
            self.assertEqual(list(range(1, len(events) + 1)),
                             [event["seq"] for event in events], case["case_id"])
            self.assertEqual(sorted((event["t"], event["seq"]) for event in events),
                             [(event["t"], event["seq"]) for event in events],
                             case["case_id"])
            observations = [e for e in events if e["kind"] == "OBSERVATION"]
            for observation in observations:
                if observation["freshness"] == "FRESH":
                    self.assertEqual(observation["seq"] - 1,
                                     observation["covers_through_seq"], case["case_id"])

    def test_operation_lifecycle_has_causal_order(self):
        for case in scenarios.build_scenarios():
            events = case["events"]
            by_id = {}
            for event in events:
                if event.get("op_id"):
                    by_id.setdefault(event["op_id"], []).append(event)
            for op_events in by_id.values():
                accepted = [e for e in op_events if e["kind"] == "ADMISSION"
                            and e.get("decision") == "ACCEPTED"]
                # Duplicate acceptance is a deliberate adversarial fixture.
                if len(accepted) > 1:
                    continue
                kinds = [e["kind"] for e in op_events]
                positions = {kind: kinds.index(kind) for kind in
                             ("ADMISSION", "START", "EFFECT", "COMPLETE_ACK")
                             if kind in kinds}
                ordered = [positions[k] for k in
                           ("ADMISSION", "START", "EFFECT", "COMPLETE_ACK")
                           if k in positions]
                self.assertEqual(sorted(ordered), ordered, str(op_events))


if __name__ == "__main__":
    unittest.main()
