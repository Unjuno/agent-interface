import unittest

from verify_successor import validate_outcome


EXPECTED = {
    "docker_engine": "29.8.0",
    "daemon_platform": "linux/x86_64",
    "image_id": "sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9",
    "image_platform": "linux/amd64",
    "python": "3.12.14",
}
RECEIPT = {key: value for key, value in EXPECTED.items() if key != "python"}
RAW = {
    "decision": "PASS_RUNTIME_BOUND_AUDIT_SCOPED",
    "observed_host_runtime": RECEIPT,
    "observed_container_python": "3.12.14",
    "baseline": {"decision": "PASS_RESULT_LEDGER_BINDING_SCOPED", "errors": []},
    "ledger_controls": {key: {"rejected": True} for key in ("drop_input_row", "input_digest", "input_path")},
    "runtime_mismatch_controls": {
        key: {"stopped": True, "semantic_audit_invoked": False, "decision": "STOP_PROVENANCE_OR_ENVIRONMENT"}
        for key in ("docker_engine", "daemon_platform", "image_id", "image_platform", "python")
    },
}


class IndependentOutcomeTests(unittest.TestCase):
    def test_exact_retained_outcome_passes(self):
        self.assertEqual(validate_outcome(RAW, RECEIPT, EXPECTED), [])

    def test_changed_receipt_is_rejected(self):
        wrong = dict(RECEIPT, docker_engine="28.5.1")
        self.assertIn("RECEIPT_RAW_MISMATCH", validate_outcome(RAW, wrong, EXPECTED))

    def test_missing_runtime_control_is_rejected(self):
        changed = dict(RAW)
        changed["runtime_mismatch_controls"] = dict(RAW["runtime_mismatch_controls"])
        changed["runtime_mismatch_controls"].pop("python")
        self.assertIn("RUNTIME_CONTROLS_MISMATCH", validate_outcome(changed, RECEIPT, EXPECTED))


if __name__ == "__main__":
    unittest.main()
