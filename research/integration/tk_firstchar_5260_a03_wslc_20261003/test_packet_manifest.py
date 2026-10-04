import hashlib
from pathlib import Path
import tempfile
import unittest
from verify_packet import manifest_errors, scope_errors


class ManifestTests(unittest.TestCase):
    def test_component_scope_cannot_be_relabelled_formal_or_replayed(self):
        run = {"disposition": "PASS_CONSTRUCTION_CUSTODY_NO_INPUT_ONLY",
               "container_invocations": 1, "apps": 8, "retries": 0,
               "input_events": 0, "first_character_formal_invocations": 0}
        self.assertEqual(scope_errors(run), [])
        for key, value in (("disposition", "PASS_FORMAL"), ("retries", 1),
                           ("container_invocations", 2), ("input_events", 1),
                           ("first_character_formal_invocations", 1)):
            self.assertTrue(scope_errors({**run, key: value}))

    def test_exact_complete_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "one.bin").write_bytes(b"exact\x00bytes\r\n")
            line = hashlib.sha256((root / "one.bin").read_bytes()).hexdigest() + "  one.bin"
            self.assertEqual(manifest_errors(root, [line]), [])
            self.assertTrue(manifest_errors(root, ["0" * 64 + "  one.bin"]))
            self.assertTrue(manifest_errors(root, [line, line]))
            self.assertTrue(manifest_errors(root, ["0" * 64 + "  ../outside"]))
            self.assertTrue(manifest_errors(root, []))
            (root / "nested").mkdir()
            (root / "nested/SHA256SUMS").write_bytes(b"unlisted evidence")
            self.assertTrue(manifest_errors(root, [line]))


if __name__ == "__main__":
    unittest.main()
