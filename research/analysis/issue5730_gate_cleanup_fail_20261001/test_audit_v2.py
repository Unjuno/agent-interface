import json
import shutil
import tempfile
import unittest
from pathlib import Path

from audit_v2 import audit_values


ROOT = Path(__file__).resolve().parent


class AuditV2MutationTests(unittest.TestCase):
    def fixture(self, mutate=None):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        for name in ("FREEZE.json", "RUN.json", "STDOUT.bin", "STDERR.bin", "EXECUTION.json",
                     "PREREG.md", "gate.py", "test_gate.py", "run_construction.py", "audit.py", "test_audit.py"):
            shutil.copyfile(ROOT / name, root / name)
        if mutate:
            run = json.loads((root / "RUN.json").read_text(encoding="utf-8"))
            mutate(run)
            (root / "RUN.json").write_text(json.dumps(run, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return temp, root

    def test_retained_failure_is_reconstructed(self):
        temp, root = self.fixture()
        with temp:
            result = audit_values(root)
        self.assertEqual(result["result"], "FAIL_CONSTRUCTION_CLEANUP_GAP")
        self.assertEqual(result["errors"], [])

    def test_omitted_case_is_rejected(self):
        temp, root = self.fixture(lambda run: run["cases"].pop())
        with temp:
            self.assertEqual(audit_values(root)["result"], "FAIL_AUDIT_INTEGRITY")

    def test_forged_aggregate_count_is_rejected(self):
        temp, root = self.fixture(lambda run: run.update(candidate_invocations=0))
        with temp:
            self.assertEqual(audit_values(root)["result"], "FAIL_AUDIT_INTEGRITY")

    def test_truncated_output_cannot_gain_scientific_hash(self):
        def mutate(run):
            row = next(item for item in run["cases"] if item["case"] == "candidate_json_truncated")
            row["outcome"]["raw_sha256"] = "a" * 64

        temp, root = self.fixture(mutate)
        with temp:
            self.assertEqual(audit_values(root)["result"], "FAIL_AUDIT_INTEGRITY")


if __name__ == "__main__":
    unittest.main(verbosity=2)
