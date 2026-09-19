import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import session_map01_v7 as session


class Map01FixtureContractTests(unittest.TestCase):
    def fixture(self, root):
        save = root / "contact.save.png"
        save.write_bytes(b"fixture")
        frame = root / "contact.source.png"
        frame.write_bytes(b"frame")
        manifest = root / "contact.json"
        manifest.write_text(json.dumps({
            "schema": session.FIXTURE_SCHEMA,
            "map": "MAP01", "skill": 1, "seed": 9,
            "vizdoom": "1.3.0", "iwad_sha256": "iwad",
            "save_file": save.name,
            "save_sha256": hashlib.sha256(save.read_bytes()).hexdigest(),
            "source_frame": frame.name,
            "source_frame_sha256": hashlib.sha256(frame.read_bytes()).hexdigest(),
            "episode_tic": 42,
            "source_observation": {"event": "observation", "exact": True},
            "setup_input_contract": session.SETUP_INPUT_CONTRACT,
        }), encoding="utf-8")
        return manifest, save

    def test_valid_hash_bound_sibling_fixture(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest, save = self.fixture(Path(directory))
            loaded, loaded_save = session.validate_fixture_manifest(
                manifest, "1.3.0", "iwad", 1)
            self.assertEqual(loaded_save, save.resolve())
            self.assertEqual(loaded["episode_tic"], 42)

    def test_tampered_save_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest, save = self.fixture(Path(directory))
            save.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                session.validate_fixture_manifest(manifest, "1.3.0", "iwad", 1)

    def test_environment_and_source_contracts_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest, _ = self.fixture(Path(directory))
            with self.assertRaisesRegex(ValueError, "engine/IWAD mismatch"):
                session.validate_fixture_manifest(manifest, "1.3.1", "iwad", 1)
            record = json.loads(manifest.read_text())
            record["source_observation"]["exact"] = False
            manifest.write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, "exact source"):
                session.validate_fixture_manifest(manifest, "1.3.0", "iwad", 1)

    def test_save_path_cannot_escape_manifest_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest, _ = self.fixture(Path(directory))
            record = json.loads(manifest.read_text())
            record["save_file"] = "../contact.zds"
            manifest.write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, "sibling PNG basename"):
                session.validate_fixture_manifest(manifest, "1.3.0", "iwad", 1)


if __name__ == "__main__":
    unittest.main()
