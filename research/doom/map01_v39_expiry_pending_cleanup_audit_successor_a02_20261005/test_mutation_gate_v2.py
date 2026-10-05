"""End-to-end mutation controls for an audit script using frozen A02 JSON."""
import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = json.loads((HERE / "results/formal_02/candidate.json").read_text())
AUDITOR = Path(sys.argv.pop(1)).resolve()


class AuditMutationGate(unittest.TestCase):
    def run_audit(self, mutate=None, optimized=False):
        data = copy.deepcopy(RAW)
        if mutate:
            mutate(data)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "results/formal_02"
            out.mkdir(parents=True)
            (out / "candidate.json").write_text(json.dumps(data))
            shutil.copyfile(AUDITOR, root / "audit_a02.py")
            command = [sys.executable]
            if optimized:
                command.append("-O")
            command.append("audit_a02.py")
            return subprocess.run(command, cwd=root, capture_output=True, text=True)


    def assert_accepted_in_both_modes(self, mutate=None):
        for optimized in (False, True):
            with self.subTest(optimized=optimized):
                self.assertEqual(self.run_audit(mutate, optimized).returncode, 0)

    def assert_rejected_in_both_modes(self, mutate):
        for optimized in (False, True):
            with self.subTest(optimized=optimized):
                self.assertNotEqual(self.run_audit(mutate, optimized).returncode, 0)

    def test_unmutated_retained_run_is_accepted(self):
        self.assert_accepted_in_both_modes()

    def test_wrong_emitted_step_is_rejected(self):
        def mutate(data):
            next(e for e in data["events"] if e["event"] == "input_release_measurement")["step"] = 9
        self.assert_rejected_in_both_modes(mutate)

    def test_wrong_emitted_intent_token_is_rejected(self):
        def mutate(data):
            next(e for e in data["events"] if e["event"] == "input_release_measurement")["intent_token"] = "foreign-token"
        self.assert_rejected_in_both_modes(mutate)

    def test_wrong_emitted_owner_id_is_rejected(self):
        def mutate(data):
            next(e for e in data["events"] if e["event"] == "input_release_measurement")["owner_id"] = "foreign-owner"
        self.assert_rejected_in_both_modes(mutate)

    def test_emitted_nonphysical_up_classification_is_rejected(self):
        def mutate(data):
            row = next(e for e in data["events"] if e["event"] == "input_release_measurement")
            row["physical_key_measurement"]["classification"] = "UNKNOWN"
        self.assert_rejected_in_both_modes(mutate)

    def test_receipt_after_terminal_is_rejected(self):
        def mutate(data):
            rows = data["events"]
            receipt = next(e for e in rows if e["event"] == "input_release_measurement")
            rows.remove(receipt)
            rows.insert(next(i for i,e in enumerate(rows) if e["event"] == "terminal") + 1, receipt)
        self.assert_rejected_in_both_modes(mutate)

    def test_held_button_in_owner_cleanup_is_rejected(self):
        def mutate(data):
            record = next(r for r in data["owner_records_after_unblock"] if r.get("reason") == "expired")
            record["buttons_down"] = [1]
        self.assert_rejected_in_both_modes(mutate)

    def test_emitted_authority_true_is_rejected(self):
        def mutate(data):
            row = next(e for e in data["events"] if e["event"] == "input_release_measurement")
            row["grants_input_authority"] = True
        self.assert_rejected_in_both_modes(mutate)

    def test_emitted_edge_down_is_rejected(self):
        def mutate(data):
            row = next(e for e in data["events"] if e["event"] == "input_release_measurement")
            row["edge"] = "down"
        self.assert_rejected_in_both_modes(mutate)

    def test_emitted_reason_conflict_is_rejected(self):
        def mutate(data):
            row = next(e for e in data["events"] if e["event"] == "input_release_measurement")
            row["reason"] = "cancelled"
        self.assert_rejected_in_both_modes(mutate)


if __name__ == "__main__":
    unittest.main(verbosity=2)
