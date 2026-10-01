"""Construction/corruption controls; no optimizer or formal data run."""
from __future__ import annotations

import base64
import hashlib
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest

_SPEC = spec_from_file_location("issue_3887_audit_under_test", Path(__file__).with_name("audit.py"))
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("cannot load sibling audit.py")
audit = module_from_spec(_SPEC)
_SPEC.loader.exec_module(audit)


def metric_for(predicted: list[int], expected: list[int], role: str) -> dict:
    packed = audit.encode_labels(predicted)
    correct = sum(a == b for a, b in zip(expected, predicted))
    return {
        "requested_role": role,
        "selected_adapter": role,
        "decision": "PROPOSE",
        "epoch": 1,
        "version": 16,
        "n": len(expected),
        "predicted_b64": base64.b64encode(packed).decode("ascii"),
        "predicted_sha256": hashlib.sha256(packed).hexdigest(),
        "correct": correct,
        "accuracy": correct / len(expected),
    }


class IndependentAuditControls(unittest.TestCase):
    def test_two_bit_round_trip(self):
        labels = [0, 1, 2, 3, 3, 2, 1, 0]
        self.assertEqual(audit.decode_labels(audit.encode_labels(labels), len(labels)), labels)

    def test_recomputes_metric_from_all_labels(self):
        expected = [0, 1, 2, 3]
        metric = metric_for([0, 1, 0, 3], expected, audit.ROLES[0])
        errors, predicted, correct = audit.check_metric(metric, expected, audit.ROLES[0], "fixture")
        self.assertEqual(errors, [])
        self.assertEqual(predicted, [0, 1, 0, 3])
        self.assertEqual(correct, 3)

    def test_prediction_payload_corruption_is_detected(self):
        expected = [0, 1, 2, 3]
        metric = metric_for(expected, expected, audit.ROLES[0])
        metric["predicted_b64"] = base64.b64encode(audit.encode_labels([3, 1, 2, 3])).decode("ascii")
        errors, _, _ = audit.check_metric(metric, expected, audit.ROLES[0], "fixture")
        self.assertIn("fixture:metric_prediction_hash", errors)
        self.assertIn("fixture:correct_count", errors)

    def test_route_and_recorded_score_corruption_are_detected(self):
        expected = [0, 1, 2, 3]
        metric = metric_for(expected, expected, audit.ROLES[0])
        metric["selected_adapter"] = audit.ROLES[1]
        metric["accuracy"] = 0.5
        errors, _, _ = audit.check_metric(metric, expected, audit.ROLES[0], "fixture")
        self.assertIn("fixture:route_or_selected_adapter", errors)
        self.assertIn("fixture:accuracy", errors)

    def test_malformed_payload_is_rejected(self):
        metric = metric_for([0, 1, 2, 3], [0, 1, 2, 3], audit.ROLES[0])
        metric["predicted_b64"] = "not base64!"
        errors, predicted, correct = audit.check_metric(metric, [0, 1, 2, 3], audit.ROLES[0], "fixture")
        self.assertIn("fixture:prediction_encoding", errors)
        self.assertIsNone(predicted)
        self.assertIsNone(correct)


if __name__ == "__main__":
    unittest.main(verbosity=2)
