"""Adversarial regression tests for the portable #3483 evidence auditor."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
ARCHIVE = HERE / "evidence-991131.tar.gz"
AUDITOR = HERE / "audit_replay.py"
EXPECTED_PASS = "PASS_SELECTION_GATED_SAVED_MOVE_SCOPED_RAW_REPLAY"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class OfflineReplayAuditTests(unittest.TestCase):
    def run_bundle(self, root):
        result = subprocess.run([sys.executable, str(AUDITOR), str(root)],
                                capture_output=True, text=True, check=False)
        return result.returncode, json.loads(result.stdout)

    def extract(self, root):
        with tarfile.open(ARCHIVE, "r:gz") as archive:
            archive.extractall(root)
        return root

    def rewrite_manifest_entry(self, root, relative):
        audit_path = root / "audit.json"
        audit = json.loads(audit_path.read_text())
        audit["raw_manifest"][relative] = digest(root / relative)
        audit_path.write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")

    def test_unmodified_archive_replays_pass_without_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.extract(Path(temp))
            before = digest(root / "audit.json")
            code, result = self.run_bundle(root)
            self.assertEqual(code, 0)
            self.assertEqual(result["disposition"], EXPECTED_PASS)
            self.assertEqual(result["raw_manifest_entries"], 62)
            self.assertTrue(result["actions_exactly_match_reply_actions"])
            self.assertTrue(result["frozen_input_shapes_match"])
            self.assertEqual(digest(root / "audit.json"), before)

    def test_mismatched_source_png_fails_even_if_manifest_is_rewritten(self):
        relative = "evidence/session/allocation/run/bridge/images/d7133d5fd77c4ceab1012b2d066800b6.png"
        with tempfile.TemporaryDirectory() as temp:
            root = self.extract(Path(temp))
            path = root / relative
            path.write_bytes(path.read_bytes() + b"tampered")
            self.rewrite_manifest_entry(root, relative)
            code, result = self.run_bundle(root)
            self.assertNotEqual(code, 0)
            self.assertNotEqual(result["disposition"], EXPECTED_PASS)
            self.assertFalse(result["selection_frame_linked_to_reply_and_authorizing_source"])

    def test_relabelled_duplicate_click_cannot_stand_in_for_keyboard_reply(self):
        relative = "evidence/session/allocation/run/actions.json"
        with tempfile.TemporaryDirectory() as temp:
            root = self.extract(Path(temp))
            path = root / relative
            rows = json.loads(path.read_text())
            rows[1] = copy.deepcopy(rows[0])
            rows[1]["stage"] = 2
            rows[1]["interaction"] = "keyboard"
            path.write_text(json.dumps(rows, sort_keys=True, indent=2) + "\n")
            self.rewrite_manifest_entry(root, relative)
            code, result = self.run_bundle(root)
            self.assertNotEqual(code, 0)
            self.assertNotEqual(result["disposition"], EXPECTED_PASS)
            self.assertFalse(result["actions_exactly_match_reply_actions"])

    def test_manifest_path_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.extract(Path(temp))
            audit_path = root / "audit.json"
            audit = json.loads(audit_path.read_text())
            audit["raw_manifest"]["../outside-bundle"] = "0" * 64
            audit_path.write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
            code, result = self.run_bundle(root)
            self.assertNotEqual(code, 0)
            self.assertNotEqual(result["disposition"], EXPECTED_PASS)
            self.assertTrue(any(item["error"] == "missing_or_outside_bundle"
                                for item in result["raw_manifest_mismatches"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
