import copy
import json
import pathlib
import subprocess
import sys
import unittest


ROOT = pathlib.Path(__file__).parent
FIXTURE = ROOT / "fixture.json"
CANDIDATE = ROOT / "candidate.py"
AUDITOR = ROOT / "audit.py"


class ObligationConservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        result = subprocess.run([sys.executable, str(CANDIDATE)], input=json.dumps(cls.fixture),
                                text=True, capture_output=True, check=True)
        cls.raw = json.loads(result.stdout)

    def audit(self, raw):
        return subprocess.run([sys.executable, str(AUDITOR), str(FIXTURE)], input=json.dumps(raw),
                              text=True, capture_output=True)

    def test_full_finite_history_and_dependency_matrix(self):
        result = self.audit(self.raw)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        summary = json.loads(result.stdout)
        self.assertEqual((summary["cases"], summary["created_obligation_ids"]), (11, 14))
        self.assertEqual(self.raw["timeout_dependency"]["outstanding"], 1)
        self.assertEqual(self.raw["timeout_dependency"]["obligations"][0]["routing"], "EXPLICITLY_ESCALATED")
        self.assertEqual(self.raw["verified_resolution"]["outstanding"], 0)

    def test_independent_work_proceeds_while_overlapping_and_unknown_hold(self):
        rows = self.raw["timeout_dependency"]["decisions"]
        self.assertFalse(rows[0]["policies"]["ledger_dependency"])
        self.assertTrue(rows[1]["policies"]["ledger_dependency"])
        self.assertFalse(rows[1]["policies"]["global_wait"])
        self.assertFalse(self.raw["unknown_footprint"]["decisions"][0]["policies"]["ledger_dependency"])

    def test_transfer_timeout_and_parent_close_never_discharge(self):
        for name in ("timeout_dependency", "accepted_transfer", "unaccepted_transfer", "parent_release_child"):
            self.assertGreater(self.raw[name]["outstanding"], 0, name)
        self.assertEqual(self.raw["accepted_transfer"]["obligations"][0]["owner"], "B")
        self.assertEqual(self.raw["unaccepted_transfer"]["obligations"][0]["owner"], "A")
        self.assertFalse(self.raw["parent_release_child"]["obligations"][0]["parent_closed"])

    def test_compensation_creates_separate_child_and_duplicate_is_rejected(self):
        items = self.raw["compensation_emits_child"]["obligations"]
        self.assertEqual({item["id"] for item in items}, {"original", "comp-effect"})
        self.assertEqual(self.raw["duplicate_compensation"]["events"][-1]["accepted"], False)

    def test_oracle_rejects_five_corruptions(self):
        mutations = []
        dropped = copy.deepcopy(self.raw)
        dropped["timeout_dependency"]["obligations"].clear()
        mutations.append(dropped)
        timeout = copy.deepcopy(self.raw)
        timeout["timeout_dependency"]["obligations"][0]["status"] = "RESOLVED_VERIFIED"
        mutations.append(timeout)
        transfer = copy.deepcopy(self.raw)
        transfer["accepted_transfer"]["outstanding"] = 0
        mutations.append(transfer)
        alias = copy.deepcopy(self.raw)
        alias["resource_alias"]["decisions"][0]["policies"]["ledger_dependency"] = True
        mutations.append(alias)
        inverse = copy.deepcopy(self.raw)
        inverse["compensation_emits_child"]["obligations"] = inverse["compensation_emits_child"]["obligations"][:1]
        mutations.append(inverse)
        for mutated in mutations:
            self.assertNotEqual(self.audit(mutated).returncode, 0)


if __name__ == "__main__":
    unittest.main()
