import unittest
from pathlib import Path

from audit import adjudicate, load_inputs


class FailClosedPreflightTests(unittest.TestCase):
    def test_source_mismatch_stops_before_delivery_or_mutations(self):
        def must_not_run(*_args):
            raise AssertionError("delivery/mutation evaluator ran after source mismatch")

        result = adjudicate(
            files={},
            preflight_errors=["INPUT_SHA256_MISMATCH:audit_plan"],
            history_errors=[],
            evaluator=must_not_run,
        )
        self.assertEqual(result["disposition"], "STOP_SOURCE_OR_FREEZE_MISMATCH")
        self.assertIsNone(result["baseline"])
        self.assertEqual(result["mutations"], {})

    def test_history_mismatch_stops_before_delivery_or_mutations(self):
        def must_not_run(*_args):
            raise AssertionError("delivery/mutation evaluator ran after freeze mismatch")

        result = adjudicate(
            files={},
            preflight_errors=[],
            history_errors=["FORMAL_FREEZE_BINDING_MISMATCH"],
            evaluator=must_not_run,
        )
        self.assertEqual(result["disposition"], "STOP_SOURCE_OR_FREEZE_MISMATCH")
        self.assertIsNone(result["baseline"])
        self.assertEqual(result["mutations"], {})


if __name__ == "__main__":
    unittest.main()
