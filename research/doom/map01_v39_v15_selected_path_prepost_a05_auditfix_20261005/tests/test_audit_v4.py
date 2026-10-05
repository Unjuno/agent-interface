import importlib.util
import hashlib
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "code" / "audit_v4.py"

def load_audit():
    spec = importlib.util.spec_from_file_location("audit_v4_under_test", AUDIT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class InputHashTests(unittest.TestCase):
    def test_hashes_parent_pre_run_and_all_frozen_inputs(self):
        audit = load_audit()
        payloads = {
            "raw": b"raw",
            "parent_a02_pre_run": b"parent pre-run",
            "parent_a02_audit_v1": b"audit v1",
            "parent_a03_audit_v2_stdout": b"audit v2 stdout",
            "parent_a03_result": b"audit v2 result",
        }
        got = audit.input_hashes(**payloads, audit_v2_source=b"audit v2 source")
        expected = {name: hashlib.sha256(value).hexdigest() for name, value in payloads.items()}
        expected["parent_a03_auditor_source"] = hashlib.sha256(b"audit v2 source").hexdigest()
        self.assertEqual(got, expected)

    def test_a05_freeze_binds_parent_and_a05_run_record(self):
        audit = load_audit()
        hashes = {"raw": "raw-hash", "parent_a02_pre_run": "pre-hash"}
        source_hash = "a05-source"
        parent = {"base_commit": audit.A02_BASE,
                  "planned_candidate_invocations": 1,
                  "planned_auditor_invocations": 1,
                  "retries": 0,
                  "source_bindings": [1] * 8}
        freeze = {"allocation": "V39-V15-PREPOST-A05-AUDIT-FIX-20261005-01",
                  "candidate_invocations_planned": 0,
                  "auditor_invocations_planned": 1,
                  "candidate_invocations_actual": 0,
                  "auditor_invocations_actual": 0,
                  "retries": 0,
                  "auditor_source_sha256": source_hash,
                  "inputs": hashes}
        self.assertEqual(audit.preregistration_errors(parent, freeze, hashes, source_hash), [])
        altered = {**freeze, "allocation": "A04"}
        self.assertIn("a05_preregistration_mismatch",
                      audit.preregistration_errors(parent, altered, hashes, source_hash))

if __name__ == "__main__":
    unittest.main(verbosity=2)
