"""Mutation controls for RUN_V2 receipt-path and value binding."""
import json
import tempfile
import unittest
from pathlib import Path

from audit_c12_v2 import audit


class AuditManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "raw").mkdir()
        source = Path(__file__).resolve().parent
        for name in (
            "composition-output.txt", "composition-exit.txt",
            "publication-control-output.txt", "publication-control-exit.txt",
            "initial-combined-suite-output.txt", "initial-combined-suite-exit.txt",
        ):
            (self.root / "raw" / name).write_bytes((source / "raw" / name).read_bytes())
        (self.root / "RUN_V2.json").write_bytes((source / "RUN_V2.json").read_bytes())
        (self.root / "SOURCE_PINS.json").write_bytes((source / "SOURCE_PINS.json").read_bytes())
        pins = json.loads((source / "SOURCE_PINS.json").read_text())
        for rel in pins:
            dest = self.root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes((source / rel).read_bytes())

    def tearDown(self):
        self.temp.cleanup()

    def test_exact_manifest_and_receipts_pass(self):
        self.assertEqual(audit(self.root)["decision"], "PASS_COMPOSITION_SCOPED")

    def test_wrong_receipt_path_fails(self):
        p = self.root / "RUN_V2.json"
        data = json.loads(p.read_text())
        data["composition_exit_receipt"] = "raw/candidate-exit.txt"
        p.write_text(json.dumps(data))
        self.assertIn("manifest_path:composition_exit_receipt", audit(self.root)["errors"])

    def test_wrong_receipt_value_fails(self):
        (self.root / "raw/composition-exit.txt").write_text("1\n")
        self.assertIn("exit_receipt_value:composition_exit_receipt", audit(self.root)["errors"])

    def test_missing_manifest_member_fails(self):
        (self.root / "raw/publication-control-exit.txt").unlink()
        self.assertIn("missing_manifest_member:publication_control_exit_receipt", audit(self.root)["errors"])

    def test_unexpected_field_fails_closed(self):
        p = self.root / "RUN_V2.json"
        data = json.loads(p.read_text())
        data["exit_receipt"] = "raw/candidate-exit.txt"
        p.write_text(json.dumps(data))
        self.assertIn("run_manifest_contract_mismatch", audit(self.root)["errors"])

    def test_changed_pinned_source_fails(self):
        pins = json.loads((self.root / "SOURCE_PINS.json").read_text())
        rel = next(iter(pins))
        (self.root / rel).write_bytes(b"mutated source\n")
        self.assertIn(f"source_pin_hash:{rel}", audit(self.root)["errors"])


if __name__ == "__main__":
    unittest.main()
