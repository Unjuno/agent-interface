"""Host-only construction tests; not counted as the WSLc experiment."""
import copy
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("receipt_auditor", HERE / "audit.py")
AUDITOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDITOR)


class ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        proc = subprocess.run([sys.executable, str(HERE / "candidate.py")], capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr)
        cls.raw = json.loads(proc.stdout)
        cls.source = (HERE / "scenarios.json").read_bytes()

    def test_candidate_truth_table(self):
        self.assertEqual(
            [(r["scenario_id"], r["intermediate_status"], r["endpoint_status"]) for r in self.raw["rows"]],
            [("valid_effect", "SUCCESS", "SEMANTICALLY_CONFIRMED"),
             ("wrong_target", "SUCCESS", "UNKNOWN"),
             ("stale_pre_state", "SUCCESS", "UNKNOWN"),
             ("noop", "SUCCESS", "UNKNOWN")],
        )

    def test_auditor_accepts_raw_and_rejects_four_mutations(self):
        accepted = AUDITOR.audit(self.raw, self.source)
        self.assertEqual(accepted["decision"], "PASS_CONTAINER_REPLAY_SCOPED")
        mutations = [
            lambda x: x["rows"][1].update(endpoint_status="SEMANTICALLY_CONFIRMED"),
            lambda x: x["rows"][0].update(scenario_id="valid_effect:other-target"),
            lambda x: x["rows"].pop(),
            lambda x: x["rows"].append(copy.deepcopy(x["rows"][0])),
        ]
        for mutate in mutations:
            changed = copy.deepcopy(self.raw)
            mutate(changed)
            self.assertNotEqual(AUDITOR.audit(changed, self.source)["decision"], "PASS_CONTAINER_REPLAY_SCOPED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
