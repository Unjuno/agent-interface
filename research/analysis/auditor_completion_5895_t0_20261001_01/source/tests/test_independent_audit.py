import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from independent_audit import (CASE_ORDER, EXPECTED_EXIT, completion_filter_accepts,
                               expected_completion_rows, fixture_identity_matches,
                               frozen_noncompletion_rows, main)


class CompletionFilterOracleTests(unittest.TestCase):
    def test_fixture_identity_must_match_frozen_expected_file(self):
        expected = json.loads(Path("target/EXPECTED.json").read_text(encoding="utf-8"))
        fixture = {"allocation": expected["allocation"], "frozen_main": expected["frozen_main"]}
        self.assertTrue(fixture_identity_matches(fixture, expected))
        self.assertFalse(fixture_identity_matches({**fixture, "frozen_main": "0" * 40}, expected))

    def test_loads_frozen_noncompletion_fixture_without_running_audit(self):
        rows = frozen_noncompletion_rows("target")
        fixture = [row for row in rows if row.get("event") == "fixture"]
        self.assertEqual(len(fixture), 1)
        self.assertEqual(fixture[0]["allocation"], "MAP01-OWNER-KEYMAP-WITNESS-5156-T3-20261001-01")
        self.assertEqual(fixture[0]["synthetic_only"], True)

    def test_registered_success_filter_uses_python_zero_equality_and_one_match(self):
        self.assertTrue(completion_filter_accepts([{"event": "runner_complete", "exit_code": 0}]))
        self.assertTrue(completion_filter_accepts([{"event": "runner_complete", "exit_code": False}]))
        self.assertTrue(completion_filter_accepts([{"event": "runner_complete", "exit_code": 0.0}]))
        self.assertTrue(completion_filter_accepts([
            {"event": "runner_complete", "exit_code": 0},
            {"event": "runner_complete", "exit_code": 1},
        ]))
        self.assertFalse(completion_filter_accepts([{"event": "runner_complete", "exit_code": None}]))
        self.assertFalse(completion_filter_accepts([{"event": "runner_complete", "exit_code": "0"}]))
        self.assertFalse(completion_filter_accepts([{"event": "runner_complete"}]))
        self.assertFalse(completion_filter_accepts([
            {"event": "runner_complete", "exit_code": 0},
            {"event": "runner_complete", "exit_code": 0},
        ]))

    def test_each_case_has_the_exact_preregistered_completion_rows(self):
        self.assertEqual(expected_completion_rows("bool_false"),
                         [{"event": "runner_complete", "exit_code": False}])
        self.assertEqual(expected_completion_rows("missing_code"),
                         [{"event": "runner_complete"}])
        self.assertEqual(expected_completion_rows("duplicate_success"),
                         [{"event": "runner_complete", "exit_code": 0},
                          {"event": "runner_complete", "exit_code": 0}])
        self.assertEqual(expected_completion_rows("success_plus_failure"),
                         [{"event": "runner_complete", "exit_code": 0},
                          {"event": "runner_complete", "exit_code": 1}])


class IndependentReceiptAuditTests(unittest.TestCase):
    def write_bundle(self, root):
        frozen_target = Path("target")
        hashes = {
            "audit_formal_x11.py": ("target_git_blob", "target_sha256"),
            "EXPECTED.json": ("expected_git_blob", "expected_sha256"),
            "test_audit_formal_x11.py": ("fixture_git_blob", "fixture_sha256"),
        }
        blobs = {
            "audit_formal_x11.py": "da805fb83f70a57ad68a0768186e214524689d40",
            "EXPECTED.json": "3d33bda096c4c8789e183e3f864ee7626e643a7e",
            "test_audit_formal_x11.py": "d1eb9a854cc810fa77ca173d7e2de287ee1bd64a",
        }
        manifest = {"allocation": "OWNER-KEYUP-AUDIT-COMPLETION-GATE-5156-T0-20261001-01",
                    "disposition": "CANDIDATE_EXPECTED", "cases": []}
        for name, (blob_field, sha_field) in hashes.items():
            data = (frozen_target / name).read_bytes()
            manifest[blob_field] = blobs[name]
            manifest[sha_field] = hashlib.sha256(data).hexdigest()
        for case_id in CASE_ORDER:
            case_dir = root / case_id
            case_dir.mkdir()
            rows = [*frozen_noncompletion_rows("target"), *expected_completion_rows(case_id)]
            raw = b"".join((json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode() for row in rows)
            (case_dir / "raw.jsonl").write_bytes(raw)
            success = EXPECTED_EXIT[case_id] == 0
            audit = {"status": "PASS_SYNTHETIC_RAW_ONLY_CLI_BOUNDARY" if success else "FAIL_AUDIT",
                     "errors": [] if success else ["runner completion sentinel missing/duplicated"],
                     "raw_sha256": hashlib.sha256(raw).hexdigest(), "raw_rows": len(rows),
                     "allocation": "MAP01-OWNER-KEYMAP-WITNESS-5156-T3-20261001-01",
                     "expected_sha256": manifest["expected_sha256"], "host_launch_receipt_sha256": None,
                     "host_launch_receipt_authenticated": False, "host_launch_receipt_bindings_valid": False,
                     "scope": "synthetic JSONL serialization/process boundary only; no X server or physical input evidence"}
            audit_bytes = (json.dumps(audit, indent=2, sort_keys=True) + "\n").encode()
            (case_dir / "audit.json").write_bytes(audit_bytes)
            stdout = (json.dumps(audit, sort_keys=True) + "\n").encode()
            (case_dir / "stdout.txt").write_bytes(stdout)
            (case_dir / "stderr.txt").write_bytes(b"")
            manifest["cases"].append({
                "case_id": case_id, "expected_exit": EXPECTED_EXIT[case_id], "actual_exit": EXPECTED_EXIT[case_id],
                "raw_path": f"{case_id}/raw.jsonl", "raw_sha256": hashlib.sha256(raw).hexdigest(),
                "audit_path": f"{case_id}/audit.json", "audit_sha256": hashlib.sha256(audit_bytes).hexdigest(),
                "stdout_path": f"{case_id}/stdout.txt", "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
                "stderr_path": f"{case_id}/stderr.txt", "stderr_sha256": hashlib.sha256(b"").hexdigest(),
            })
        manifest_path = root / "candidate_manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        return manifest_path

    def test_accepts_complete_preregistered_artifact_bundle(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self.write_bundle(root)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(str(manifest), "target"), 0)

    def test_rejects_raw_mutation_after_candidate_without_rehash(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self.write_bundle(root)
            raw = root / "control" / "raw.jsonl"
            raw.write_bytes(raw.read_bytes() + b" ")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(str(manifest), "target"), 1)


if __name__ == "__main__":
    unittest.main()
