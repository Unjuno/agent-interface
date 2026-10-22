"""Focused regression of the complete typed-observation module, no GUI calls."""
from copy import deepcopy
import json
import math
import unittest
from doom_typed_observation_v1 import build_action_snapshot
from action_validity_admission_v1 import action_fingerprint, evaluate_action_validity


def fixture():
    binding = {"focus": 7, "surface": 7, "geometry": [0, 0, 640, 480]}
    action = {"op": "observe_only"}
    signals = {name: {"signal_id": name, "sequence": 2,
                        "capture_ns": 1_000_000_000, "binding": deepcopy(binding),
                        "status": "observed", "value": val}
               for name, val in (("health", 100), ("ammo", 50))}
    event = {"event": "typed_observation", "schema": "doom-typed-observation-v1",
             "id": "a17-fixture", "step": 0, "sequence": 2,
             "capture_ns": 1_000_000_000, "pointer_binding": binding,
             "typed_extraction_started_ns": 1_001_000_000,
             "typed_ready_ns": 1_010_000_000, "capture_to_typed_ready_ms": 10.0,
             "frame_rgb_sha256": "a" * 64, "frame_size": [640, 480],
             "artifact_published": False, "grants_input_authority": False,
             "signals": signals}
    contract = {"format": "action-validity-contract-v1",
                "action_fingerprint": action_fingerprint(action),
                "source": {"sequence": 1, "capture_ns": 900_000_000,
                           "binding": deepcopy(binding),
                           "signals": {"health": {"status": "observed", "value": 100}}},
                "max_current_age_ms": 100,
                "predicates": [{"signal_id": "health", "operator": "minimum", "value": 90}]}
    return event, contract, action


class ElapsedTests(unittest.TestCase):
    def test_rejects_nan_from_default_json(self):
        event, contract, _ = fixture()
        event['capture_to_typed_ready_ms'] = json.loads('NaN')
        with self.assertRaises(ValueError):
            build_action_snapshot(event, contract)

    def test_rejects_infinite_elapsed(self):
        for v in (math.inf, -math.inf):
            with self.subTest(value=str(v)):
                event, contract, _ = fixture()
                event['capture_to_typed_ready_ms'] = v
                with self.assertRaises(ValueError):
                    build_action_snapshot(event, contract)

    def test_preserves_finite_tolerance_and_nonmutation(self):
        for v in (10, 10.0, 10.0000000005):
            with self.subTest(value=v):
                event, contract, _ = fixture()
                event['capture_to_typed_ready_ms'] = v
                before = json.dumps([event, contract], sort_keys=True)
                result = build_action_snapshot(event, contract)
                self.assertEqual(result['signals']['health']['value'], 100)
                self.assertEqual(json.dumps([event, contract], sort_keys=True), before)

    def test_rejects_mismatch_and_wrong_type(self):
        for v in (10.000000002, True, None, '10', [], {}):
            with self.subTest(value=repr(v)):
                event, contract, _ = fixture()
                event['capture_to_typed_ready_ms'] = v
                with self.assertRaises(ValueError):
                    build_action_snapshot(event, contract)

    def test_rejects_reversed_bracket_and_epoch(self):
        for key in ('bracket', 'epoch'):
            with self.subTest(key=key):
                event, contract, _ = fixture()
                if key == 'bracket':
                    event['typed_ready_ns'] = event['capture_ns'] - 1
                else:
                    event['signals']['health']['sequence'] = 3
                with self.assertRaises(ValueError):
                    build_action_snapshot(event, contract)

    def test_integer_age_gate_still_rejects_stale(self):
        event, contract, action = fixture()
        snapshot = build_action_snapshot(event, contract)
        current = evaluate_action_validity(action, contract, snapshot, 1_050_000_000)
        stale = evaluate_action_validity(action, contract, snapshot, 1_200_000_000)
        self.assertEqual(current['status'], 'VALID_CURRENT')
        self.assertEqual(stale['status'], 'REJECTED_STALE')
        self.assertIs(current['grants_input_authority'], False)
        self.assertIs(stale['grants_input_authority'], False)

if __name__ == '__main__':
    unittest.main(verbosity=2)
