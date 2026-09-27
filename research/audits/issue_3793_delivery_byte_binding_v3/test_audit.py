import unittest

from audit import (
    AUDITOR_PATH,
    EXPECTED,
    PLAN_PATH,
    adjudicate,
    validate_freeze_source_hashes,
)


class FreezeGateTests(unittest.TestCase):
    def test_full_repository_path_keys_match_frozen_hashes(self):
        freeze = {"sha256": {
            PLAN_PATH: EXPECTED["audit_plan"],
            AUDITOR_PATH: EXPECTED["audit_source"],
        }}
        self.assertEqual(validate_freeze_source_hashes(freeze), [])

    def test_basename_keys_are_not_accepted_as_frozen_provenance(self):
        freeze = {"sha256": {
            "PLAN.md": EXPECTED["audit_plan"],
            "audit.py": EXPECTED["audit_source"],
        }}
        self.assertEqual(
            set(validate_freeze_source_hashes(freeze)),
            {"FROZEN_PLAN_HASH_MISMATCH", "FROZEN_AUDITOR_HASH_MISMATCH"},
        )

    def test_source_stop_short_circuits_all_delivery_evaluation(self):
        def must_not_run(*_args):
            raise AssertionError("delivery evaluator ran after source mismatch")

        result = adjudicate(
            files={},
            preflight_errors=["INPUT_SHA256_MISMATCH:audit_plan"],
            history_errors=[],
            evaluator=must_not_run,
        )
        self.assertEqual(result["disposition"], "STOP_SOURCE_OR_FREEZE_MISMATCH")
        self.assertIsNone(result["baseline"])
        self.assertEqual(result["mutations"], {})

    def test_history_stop_short_circuits_all_delivery_evaluation(self):
        def must_not_run(*_args):
            raise AssertionError("delivery evaluator ran after freeze mismatch")

        result = adjudicate(
            files={},
            preflight_errors=[],
            history_errors=["FROZEN_PLAN_HASH_MISMATCH"],
            evaluator=must_not_run,
        )
        self.assertEqual(result["disposition"], "STOP_SOURCE_OR_FREEZE_MISMATCH")
        self.assertIsNone(result["baseline"])
        self.assertEqual(result["mutations"], {})


if __name__ == "__main__":
    unittest.main()
