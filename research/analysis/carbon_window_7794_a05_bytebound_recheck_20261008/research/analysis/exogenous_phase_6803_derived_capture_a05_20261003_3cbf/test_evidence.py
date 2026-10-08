"""Post-run custody/runtime tests, separate from the frozen formal sources."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent


class EvidenceTests(unittest.TestCase):
    def load(self):
        path = ROOT / "verify_evidence.py"
        self.assertTrue(path.is_file(), "missing post-run evidence verifier")
        spec = importlib.util.spec_from_file_location("a05_evidence", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_actual_container_receipts_have_exact_observed_limits(self):
        module = self.load()
        for role in ("candidate", "legacy", "auditor"):
            inspection = json.loads((ROOT / "formal_02" / (role + ".inspect.json")).read_text())[0]
            receipt = json.loads((ROOT / "formal_02" / (role + ".receipt.json")).read_text())
            observed = {name: (ROOT / "formal_02" / role / name).read_text().strip()
                        for name in ("memory.max", "cpu.max")}
            module.validate_runtime(role, inspection, receipt, observed)

    def test_runtime_verifier_rejects_disabled_isolation_and_forged_limits(self):
        module = self.load()
        inspection = json.loads((ROOT / "formal_02/candidate.inspect.json").read_text())[0]
        receipt = json.loads((ROOT / "formal_02/candidate.receipt.json").read_text())
        limits = {"memory.max": "536870912", "cpu.max": "100000 100000"}
        for key, value in (("NetworkMode", "default"), ("ReadonlyRootfs", False), ("Memory", 0)):
            changed = copy.deepcopy(inspection)
            changed["HostConfig"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                module.validate_runtime("candidate", changed, receipt, limits)
        with self.assertRaises(ValueError):
            module.validate_runtime("candidate", inspection, receipt,
                                    dict(limits, **{"memory.max": "max"}))


if __name__ == "__main__":
    unittest.main()
