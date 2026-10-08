"""Nine corruption controls for the retained A02 release receipt audit."""
import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RAW_PATH = ROOT / "research/doom/map01_v39_expiry_pending_cleanup_audit_successor_a01_20261005/results/formal_02/candidate.json"
RAW = json.loads(RAW_PATH.read_text(encoding="utf-8"))
if len(sys.argv) != 2:
    raise RuntimeError("pass the audit script path as the only argument")
AUDITOR = Path(sys.argv.pop()).resolve()


def emitted_receipt(data):
    return next(row for row in data["events"] if row.get("event") == "input_release_measurement")


class AuditMutationGateV2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.auditor = AUDITOR

    def run_audit(self, mutate=None, optimized=False):
        data = copy.deepcopy(RAW)
        if mutate:
            mutate(data)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "results/formal_02"
            out.mkdir(parents=True)
            (out / "candidate.json").write_text(json.dumps(data), encoding="utf-8")
            shutil.copyfile(self.auditor, root / "audit_successor.py")
            command = [sys.executable]
            if optimized:
                command.append("-O")
            command.append("audit_successor.py")
            return subprocess.run(command, cwd=root, capture_output=True, text=True)

    def assert_accepted_in_both_modes(self, mutate=None):
        for optimized in (False, True):
            with self.subTest(optimized=optimized):
                result = self.run_audit(mutate, optimized)
                self.assertEqual(result.returncode, 0, result.stderr)

    def assert_rejected_in_both_modes(self, mutate):
        for optimized in (False, True):
            with self.subTest(optimized=optimized):
                result = self.run_audit(mutate, optimized)
                self.assertNotEqual(result.returncode, 0, result.stdout)

    def test_unchanged_raw_is_accepted(self):
        self.assert_accepted_in_both_modes()

    def test_wrong_emitted_step_is_rejected(self):
        def mutate(data):
            emitted_receipt(data)["step"] = 9
        self.assert_rejected_in_both_modes(mutate)

    def test_wrong_emitted_intent_token_is_rejected(self):
        def mutate(data):
            emitted_receipt(data)["intent_token"] = "foreign-token"
        self.assert_rejected_in_both_modes(mutate)

    def test_wrong_emitted_owner_id_is_rejected(self):
        def mutate(data):
            emitted_receipt(data)["owner_id"] = "foreign-owner"
        self.assert_rejected_in_both_modes(mutate)

    def test_emitted_nonphysical_up_classification_is_rejected(self):
        def mutate(data):
            emitted_receipt(data)["physical_key_measurement"]["classification"] = "UNKNOWN"
        self.assert_rejected_in_both_modes(mutate)

    def test_receipt_after_terminal_is_rejected(self):
        def mutate(data):
            rows = data["events"]
            receipt = emitted_receipt(data)
            rows.remove(receipt)
            terminal_index = next(i for i, row in enumerate(rows) if row.get("event") == "terminal")
            rows.insert(terminal_index + 1, receipt)
        self.assert_rejected_in_both_modes(mutate)

    def test_held_button_in_owner_cleanup_is_rejected(self):
        def mutate(data):
            row = next(r for r in data["owner_records_after_unblock"] if r.get("reason") == "expired")
            row["buttons_down"] = [1]
        self.assert_rejected_in_both_modes(mutate)

    def test_emitted_authority_metadata_is_rejected(self):
        def mutate(data):
            emitted_receipt(data)["grants_input_authority"] = True
        self.assert_rejected_in_both_modes(mutate)

    def test_conflicting_emitted_edge_metadata_is_rejected(self):
        def mutate(data):
            emitted_receipt(data)["edge"] = "down"
        self.assert_rejected_in_both_modes(mutate)

    def test_conflicting_emitted_reason_is_rejected(self):
        def mutate(data):
            emitted_receipt(data)["reason"] = "cancelled"
        self.assert_rejected_in_both_modes(mutate)

    def test_coherent_noncanonical_receipt_metadata_is_rejected(self):
        def mutate(data):
            emitted = emitted_receipt(data)
            owner = next(r for r in data["owner_records_after_unblock"] if r.get("reason") == "expired")
            owner_row = owner["per_key_release_measurements"][0]
            for receipt in (emitted, owner_row):
                receipt["grants_input_authority"] = True
                receipt["edge"] = "down"
                receipt["reason"] = "cancelled"
        self.assert_rejected_in_both_modes(mutate)


if __name__ == "__main__":
    unittest.main(verbosity=2)
