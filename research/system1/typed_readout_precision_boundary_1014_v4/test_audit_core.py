import copy
import unittest

from audit_core import corruption_controls, validate_result


def fixture():
    result = {
        "allocation": "typed-readout-precision-boundary-1014-v4-20260928-01",
        "status": "CONSTRUCTION_COMPLETE", "answer_ids": list(range(15, 23)),
        "answer_token_ids_verified": True, "modes": {}, "rows": [],
    }
    for mode in ("fp16", "bf16", "fp32"):
        mode_rows = []
        for bundle, slot in (("B00", 0), ("B00", 7), ("B00", 15),
                             ("B17", 0), ("B17", 7), ("B17", 15),
                             ("B63", 0), ("B63", 7), ("B63", 15)):
            full = [float(i) for i in range(8)]
            cached = list(full)
            row = {"mode": mode, "bundle_id": bundle, "slot": slot,
                   "full_logits": full, "cached_logits": cached,
                   "comparison": {"max_abs": 0.0, "max_rel": 0.0,
                                  "argmax_equal": True, "within_tolerance": True},
                   "cache_isolation": True}
            result["rows"].append(row)
            mode_rows.append(row)
        result["modes"][mode] = {"rows": 9, "all_within_tolerance": True,
                                 "all_winners_equal": True, "all_cache_isolation": True,
                                 "dtype": "fixture", "peak_cuda_bytes": 0}
    return result


class AuditCoreTests(unittest.TestCase):
    def test_accepts_complete_fixture(self):
        validate_result(fixture())

    def test_rejects_each_frozen_corruption(self):
        self.assertEqual(corruption_controls(fixture()), 5)

    def test_rejects_missing_mode(self):
        data = copy.deepcopy(fixture())
        del data["modes"]["bf16"]
        with self.assertRaises(AssertionError):
            validate_result(data)


if __name__ == "__main__":
    unittest.main(verbosity=2)

