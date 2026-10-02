import copy
import json
import unittest
from audit import validate


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.fixture = {"models": [{"name": "qwen3:4b", "manifest_rel": "m/qwen3/4b",
                                   "manifest_sha256": "a" * 64, "schema_version": 2,
                                   "media_type": "manifest", "blobs": [{"digest": "sha256:" + "b" * 64,
                                   "path": "blobs/sha256-" + "b" * 64, "size": 123}]}]}
        self.fixture_bytes = json.dumps(self.fixture, sort_keys=True).encode()
        self.raw = {"schema_version": 1,
                    "fixture_sha256": __import__("hashlib").sha256(self.fixture_bytes).hexdigest(),
                    "mount": {"mountpoint": "/models", "options": ["ro", "relatime"],
                              "readonly": True, "matching_mount_records": 1},
                    "models": [{"name": "qwen3:4b", "present": True,
                                "manifest_rel": "m/qwen3/4b", "manifest_sha256": "a" * 64,
                                "schema_version": 2, "media_type": "manifest",
                                "blobs": [{"digest": "sha256:" + "b" * 64,
                                           "path": "blobs/sha256-" + "b" * 64,
                                           "declared_bytes": 123, "present": True,
                                           "observed_bytes": 123}]}],
                    "errors": [], "blob_content_hashed": False, "model_loaded": False}

    def test_valid_raw_passes(self):
        self.assertEqual(validate(self.fixture_bytes, self.raw), [])

    def test_writable_mount_rejected(self):
        raw = copy.deepcopy(self.raw); raw["mount"]["options"] = ["rw"]; raw["mount"]["readonly"] = False
        self.assertIn("mount_not_readonly", validate(self.fixture_bytes, raw))

    def test_manifest_mutation_rejected(self):
        raw = copy.deepcopy(self.raw); raw["models"][0]["manifest_sha256"] = "c" * 64
        self.assertIn("manifest_sha256:qwen3:4b", validate(self.fixture_bytes, raw))

    def test_missing_model_rejected(self):
        raw = copy.deepcopy(self.raw); raw["models"] = []
        self.assertIn("model_coverage", validate(self.fixture_bytes, raw))

    def test_blob_size_mutation_rejected(self):
        raw = copy.deepcopy(self.raw); raw["models"][0]["blobs"][0]["observed_bytes"] = 124
        self.assertTrue(any(e.startswith("blob_identity_or_size:") for e in validate(self.fixture_bytes, raw)))


if __name__ == "__main__":
    unittest.main()
