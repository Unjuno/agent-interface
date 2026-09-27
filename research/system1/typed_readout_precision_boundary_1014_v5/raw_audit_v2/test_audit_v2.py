"""Tests use unittest checks and explicit exceptions, not Python assert."""
import copy
import json
import unittest

from audit_core_v2 import AuditValidationError, corruption_controls, validate_result
from audit_raw_v2 import verify_result_bytes


def make_fixture():
    modes = {name: {"rows": 9, "all_within_tolerance": True,
                    "all_winners_equal": True, "all_cache_isolation": True}
             for name in ("fp16", "bf16", "fp32")}
    rows = []
    for mode in modes:
        for bundle in ("B00", "B17", "B63"):
            for slot in (0, 7, 15):
                logits = [1.0 + i for i in range(8)]
                rows.append({"mode": mode, "bundle_id": bundle, "slot": slot,
                             "full_logits": logits, "cached_logits": logits.copy(),
                             "comparison": {"max_abs": 0.0, "max_rel": 0.0,
                                            "argmax_equal": True, "within_tolerance": True},
                             "cache_isolation": True})
    return {"allocation": "typed-readout-precision-boundary-1014-v5-20260928-01",
            "status": "CONSTRUCTION_COMPLETE", "answer_ids": list(range(15, 23)),
            "answer_token_ids_verified": True, "modes": modes, "rows": rows}


class AuditV2Tests(unittest.TestCase):
    def test_valid_fixture_and_corruption_controls(self):
        data = make_fixture()
        validate_result(data)
        self.assertEqual(corruption_controls(data), 5)

    def test_self_consistent_raw_mutation_is_rejected_by_byte_pin(self):
        data = make_fixture()
        for row in data["rows"]:
            row["full_logits"] = [x + 1.0 for x in row["full_logits"]]
            row["cached_logits"] = [x + 1.0 for x in row["cached_logits"]]
        validate_result(data)
        mutated = (json.dumps(data, separators=(",", ":")) + "\n").encode()
        with self.assertRaisesRegex(SystemExit, "STOP_RESULT_HASH_MISMATCH"):
            verify_result_bytes(mutated)

    def test_digest_gate_rejects_non_exact_bytes(self):
        with self.assertRaises(SystemExit):
            verify_result_bytes(b"{}\n")

    def test_wrong_allocation_fails_with_explicit_exception(self):
        data = make_fixture()
        data["allocation"] = "wrong"
        with self.assertRaises(AuditValidationError):
            validate_result(data)


if __name__ == "__main__":
    unittest.main(verbosity=2)

