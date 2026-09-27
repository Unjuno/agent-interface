import unittest

from audit_core import corruption_controls, validate_result


class AuditCoreTests(unittest.TestCase):
    def setUp(self):
        self.result = {
            "allocation": "typed-readout-precision-boundary-1014-v5-20260928-01",
            "status": "CONSTRUCTION_COMPLETE",
            "answer_ids": list(range(15, 23)),
            "answer_token_ids_verified": True,
            "modes": {
                mode: {"rows": 9, "all_within_tolerance": mode == "fp32",
                       "all_winners_equal": True, "all_cache_isolation": True}
                for mode in ("fp16", "bf16", "fp32")
            },
            "rows": [],
        }
        bundles = ("B00", "B17", "B63")
        slots = (0, 7, 15)
        for mode in ("fp16", "bf16", "fp32"):
            for bundle in bundles:
                for slot in slots:
                    logits = [1.0 + i for i in range(8)]
                    self.result["rows"].append({
                        "mode": mode, "bundle_id": bundle, "slot": slot,
                        "full_logits": logits, "cached_logits": logits.copy(),
                        "comparison": {"max_abs": 0.0, "max_rel": 0.0,
                                       "argmax_equal": True, "within_tolerance": True},
                        "cache_isolation": True,
                    })

    def test_accepts_complete_fixture(self):
        validate_result(self.result)

    def test_rejects_each_frozen_corruption(self):
        self.assertEqual(corruption_controls(self.result), 5)

    def test_rejects_missing_mode(self):
        mutated = dict(self.result)
        mutated["modes"] = dict(self.result["modes"])
        del mutated["modes"]["fp16"]
        with self.assertRaises((AssertionError, KeyError, TypeError, ValueError)):
            validate_result(mutated)


if __name__ == "__main__":
    unittest.main()
