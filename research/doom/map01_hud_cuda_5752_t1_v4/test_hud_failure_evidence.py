import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("gpu_hud_runner.py")
SPEC = importlib.util.spec_from_file_location("gpu_hud_runner_under_test", SCRIPT)
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)
AUDIT_SPEC = importlib.util.spec_from_file_location("gpu_hud_audit_under_test", SCRIPT.with_name("audit.py"))
audit = importlib.util.module_from_spec(AUDIT_SPEC)
AUDIT_SPEC.loader.exec_module(audit)


class CandidateFailureEvidenceTests(unittest.TestCase):
    def test_candidate_and_auditor_identity_comes_from_frozen_allocation(self):
        freeze = {"allocation": "GPU-HUD-CUDA-5752-20261001-04", "base_main_sha": "f" * 40}
        self.assertEqual(runner.frozen_identity(freeze), (freeze["allocation"], freeze["base_main_sha"]))
        self.assertEqual(audit.frozen_identity(freeze), (freeze["allocation"], freeze["base_main_sha"]))

    def test_runner_stops_before_output_when_durable_reserve_is_short(self):
        self.assertEqual(runner.disk_gate_status(67108863, 67108864), "STOP_INSUFFICIENT_DISK_SPACE")
        self.assertEqual(runner.disk_gate_status(67108864, 67108864), "PREFLIGHT_OK")

    def test_first_parity_mismatch_leaves_classified_partial_raw_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "candidate_result.json"
            compared = []

            def compare(_cpu, gpu):
                compared.append(gpu["ordinal"])
                return gpu["ordinal"] != 2

            rows = [
                {"ordinal": 1, "cpu": {"ordinal": 1}, "gpu": {"ordinal": 1}},
                {"ordinal": 2, "cpu": {"ordinal": 2}, "gpu": {"ordinal": 2}},
                {"ordinal": 3, "cpu": {"ordinal": 3}, "gpu": {"ordinal": 3}},
            ]

            disposition = runner.write_parity_failure_evidence(output, rows, compare)

            self.assertEqual(compared, [1, 2])
            self.assertEqual(disposition, "FAIL_CUDA_READER_MISMATCH")
            self.assertTrue(output.is_file())
            evidence = __import__("json").loads(output.read_text(encoding="utf-8"))
            self.assertEqual(evidence["candidate_disposition"], "FAIL_CUDA_READER_MISMATCH")
            self.assertEqual(evidence["compared_rows"], 2)
            self.assertEqual(evidence["rows"], rows[:2])
            self.assertEqual(evidence["mismatch_ordinal"], 2)


if __name__ == "__main__":
    unittest.main()
