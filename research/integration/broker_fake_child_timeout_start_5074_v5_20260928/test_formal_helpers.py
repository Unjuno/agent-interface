from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from formal import (preflight_command, require_fresh_paths,
                    verify_frozen_sources, verify_source_identity,
                    write_receipt_exclusive)


class FormalFreshnessTest(unittest.TestCase):
    def test_frozen_source_hashes_match_current_files(self):
        hashes = verify_frozen_sources()
        self.assertEqual(len(hashes), len(__import__("json").loads(
            Path(__file__).with_name("FREEZE.json").read_text())[
                "source"]["sha256"]))

    def test_source_commit_sha_must_equal_pinned_main(self):
        main = __import__("json").loads(
            Path(__file__).with_name("FREEZE.json").read_text())["base_main"]
        verify_source_identity(main, main)
        with self.assertRaises(ValueError):
            verify_source_identity(main, "0" * 40)
        with self.assertRaises(ValueError):
            verify_source_identity("0" * 40, "0" * 40)

    def test_formal_main_calls_source_identity_gate(self):
        source = Path(__file__).with_name("formal.py").read_text(encoding="utf-8")
        self.assertIn("verify_source_identity(args.observed_main, args.source_commit_sha)", source)

    def test_rejects_existing_formal_or_audit_output(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            formal_out = root / "formal"
            audit_out = root / "audit"
            audit_out.mkdir()
            with self.assertRaises(FileExistsError):
                require_fresh_paths(formal_out, audit_out)

    def test_receipt_is_exclusive_and_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            receipt = Path(td) / "invocation.json"
            write_receipt_exclusive(receipt, {"command": ["docker", "run"]})
            original = receipt.read_text(encoding="utf-8")
            with self.assertRaises(FileExistsError):
                write_receipt_exclusive(receipt, {"command": ["changed"]})
            self.assertEqual(receipt.read_text(encoding="utf-8"), original)

    def test_dry_preflight_returns_command_without_creating_receipt_or_outputs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "src"
            study = root / "study"
            release = root / "release.json"
            source.mkdir(); study.mkdir(); release.write_text("{}", encoding="utf-8")
            out, audit, receipt = root / "formal", root / "audit", root / "receipt.json"
            result = preflight_command(source, study, release, out, audit, receipt,
                                      ["docker", "run", "--network=none"])
            self.assertEqual(result["command"], ["docker", "run", "--network=none"])
            self.assertFalse(out.exists())
            self.assertFalse(audit.exists())
            self.assertFalse(receipt.exists())

    def test_preflight_rejects_existing_audit_output_before_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "src"; source.mkdir()
            study = root / "study"; study.mkdir()
            release = root / "release.json"; release.write_text("{}", encoding="utf-8")
            audit = root / "audit"; audit.mkdir()
            receipt = root / "receipt.json"
            with self.assertRaises(FileExistsError):
                preflight_command(source, study, release, root / "formal", audit,
                                  receipt, ["docker", "run"])
            self.assertFalse(receipt.exists())


if __name__ == "__main__":
    unittest.main()
