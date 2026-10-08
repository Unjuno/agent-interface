"""Construction checks only; no formal candidate or resource allocation."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ScheduleConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.auditor = load("audit")
        cls.raw = json.loads((HERE / "raw.json").read_text())
        cls.result = cls.auditor.audit(cls.raw)

    def test_full_grid_and_event_commitments_replay(self):
        self.assertEqual(len(self.raw["cells"]), 98)
        self.assertEqual(self.result["cells_reconstructed"], 98)
        self.assertEqual(self.result["pairs_reconstructed"], 8820)
        self.assertEqual(self.result["arms_reconstructed"], 17640)
        self.assertEqual(self.result["errors"], [])

    def test_event_commitment_mutation_is_rejected(self):
        mutated = copy.deepcopy(self.raw)
        mutated["cells"][0]["pairs"][0]["probe"]["event_sha256"] = "0" * 64
        self.assertIn("event_digest:0:0:probe", self.auditor.audit(mutated)["errors"])

    def test_pair_deletion_is_rejected(self):
        mutated = copy.deepcopy(self.raw)
        mutated["cells"][0]["pairs"].pop()
        self.assertIn("pair_inventory:0", self.auditor.audit(mutated)["errors"])


if __name__ == "__main__":
    unittest.main()
