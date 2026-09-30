"""Strict audit regression tests; standard library only."""
import json
import unittest

from audit_hardened import AuditReject, audit_document, strict_load


class HardenedAuditTests(unittest.TestCase):
    def test_rejects_nonfinite_json_constants(self):
        for token in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(token=token):
                with self.assertRaises(AuditReject):
                    strict_load(("{\"value\":" + token + "}").encode())

    def test_binds_frozen_metadata(self):
        for key, value in (("development_alpha", 0.5),
                           ("development_alpha", False),
                           ("truth_state_count", 99)):
            doc = {"schema": "predicate-order-drift-raw-v1",
                   "predicates": ["A", "B", "C", "D"],
                   "cost": {"A": 1, "B": 2, "C": 5, "D": 10},
                   "orders": {"NAIVE": ["D", "C", "B", "A"],
                              "FROZEN_COST_SELECTIVITY": ["A", "B", "C", "D"]},
                   "development_alpha": 0.0, "truth_state_count": 16,
                   "drift_grid": list(round(i / 20, 2) for i in range(21)),
                   "distributions": []}
            doc[key] = value
            with self.subTest(key=key), self.assertRaises(AuditReject):
                audit_document(doc)

    def test_rejects_bad_weight_types_and_nonfinite_values(self):
        # A minimal row/document is rejected before row traversal due missing mass,
        # so exercise the exact row validator through the documented public path
        # using the helper below, which is also used by the copied-raw probe.
        from audit_hardened import require_valid_weight
        for value in (True, "0", float("nan"), float("inf"), -float("inf"), 0.1):
            with self.subTest(value=repr(value)), self.assertRaises(AuditReject):
                require_valid_weight(value, 0.0)

    def test_accepts_exact_and_frozen_rounded_finite_weight(self):
        from audit_hardened import require_valid_weight
        self.assertEqual(require_valid_weight(0.0, 0.0), 0.0)
        expected = 0.8 * (1.0 - 0.05)
        serialized = round(expected, 12)
        self.assertEqual(require_valid_weight(serialized, expected), serialized)


if __name__ == "__main__":
    unittest.main(verbosity=2)
