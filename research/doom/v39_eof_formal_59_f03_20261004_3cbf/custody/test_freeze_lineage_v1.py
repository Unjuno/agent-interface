"""Corruption controls for the offline F03 freeze-lineage verifier."""
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest import mock

import freeze_lineage_v1 as lineage

HERE = Path(__file__).resolve().parent
ARCHIVES = {
    "predecessor": HERE / "f03-final-freeze-40b57f74f4.tar",
    "current_final": HERE / "f03-formal-freeze-6d8387caa8.tar",
}


def members(path):
    result = {}
    with tarfile.open(path, "r:") as bundle:
        for item in bundle.getmembers():
            if item.isdir():
                continue
            stream = bundle.extractfile(item)
            if stream is None:
                raise AssertionError(f"unreadable member {item.name}")
            result[item.name] = stream.read()
    return result


class FreezeLineageTests(unittest.TestCase):
    def test_both_frozen_archives_match_their_authenticated_source_trees(self):
        for name, path in ARCHIVES.items():
            with self.subTest(name=name):
                result = lineage.verify_lineage(name, members(path))
                self.assertTrue(result["member_git_blobs_match_source_tree"])
                self.assertEqual(result["source_commit_object_available"],
                                 name == "predecessor")

    def test_archive_member_corruption_fails_source_tree_binding(self):
        data = members(ARCHIVES["current_final"])
        path = next(iter(data))
        data[path] += b"x"
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            lineage.verify_lineage("current_final", data)

    def test_jointly_replaced_member_and_manifest_still_fails_pinned_tree(self):
        """A mutable fixture plus its matching mutable digest is not authority."""
        original_manifest = lineage.MANIFESTS["current_final"]["snapshot"]
        original_bytes = original_manifest.read_bytes()
        archive_data = members(ARCHIVES["current_final"])
        member_path = next(iter(archive_data))
        old_digest = __import__("hashlib").sha256(archive_data[member_path]).hexdigest()
        archive_data[member_path] += b"jointly-substituted"
        new_digest = __import__("hashlib").sha256(archive_data[member_path]).hexdigest()
        manifest_bytes = original_bytes.replace(
            f"{old_digest}  {member_path}".encode(),
            f"{new_digest}  {member_path}".encode(),
        )
        self.assertNotEqual(manifest_bytes, original_bytes)

        with tempfile.TemporaryDirectory() as temp:
            mutated_manifest = Path(temp) / "PRELAUNCH_FREEZE.md"
            mutated_manifest.write_bytes(manifest_bytes)
            with mock.patch.dict(
                lineage.MANIFESTS["current_final"],
                {"snapshot": mutated_manifest},
            ):
                # The attacker can update a free-standing manifest and archive
                # digest, but cannot rewrite the hard-coded historical commit,
                # Git object witness, or authenticated source-tree blob.
                with self.assertRaisesRegex(ValueError, "snapshot does not match"):
                    lineage.verify_lineage("current_final", archive_data)

    def test_witness_object_corruption_fails_git_object_hash(self):
        payload = json.loads(lineage.WITNESS.read_text(encoding="utf-8"))
        oid, record = next(iter(payload["objects"].items()))
        record["data_b64"] = record["data_b64"][:-4] + "AAAA"
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "witness.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with mock.patch.object(lineage, "WITNESS", path):
                with self.assertRaisesRegex(ValueError, "invalid witnessed Git object"):
                    lineage.load_objects()

    def test_manifest_snapshot_corruption_fails_blob_binding(self):
        original = lineage.MANIFESTS["predecessor"]["snapshot"]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.md"
            path.write_bytes(original.read_bytes() + b"tamper")
            with mock.patch.dict(lineage.MANIFESTS["predecessor"], {"snapshot": path}):
                with self.assertRaisesRegex(ValueError, "snapshot does not match"):
                    lineage.verify_lineage("predecessor", members(ARCHIVES["predecessor"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
