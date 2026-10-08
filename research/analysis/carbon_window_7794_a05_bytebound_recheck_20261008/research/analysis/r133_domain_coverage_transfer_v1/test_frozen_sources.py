import json
import pathlib
import unittest

import subprocess

from frozen_sources import SOURCES, load_inputs_from_payload


class FrozenSourcesTests(unittest.TestCase):
    def test_payload_loader_verifies_exact_frozen_git_blob_bytes(self):
        repository = pathlib.Path(__file__).resolve().parents[2]
        sources = {}
        for name, (_, blob) in SOURCES.items():
            sources[name] = subprocess.run(
                ["git", "cat-file", "blob", blob], cwd=repository,
                check=True, capture_output=True,
            ).stdout.decode("utf-8")
        payload = json.dumps({"base_commit": "6968d45197c6a29e717a9281dcd050be1eed90c7", "sources": sources}).encode()
        inputs, provenance = load_inputs_from_payload(payload)
        self.assertEqual(set(inputs), {"physical", "occupancy", "feedback", "calc"})
        self.assertEqual(provenance["base_commit"], "6968d45197c6a29e717a9281dcd050be1eed90c7")
        self.assertEqual(inputs["physical"]["formal"]["actuations"], 6)
        self.assertEqual(inputs["occupancy"]["runs"]["map01-v39-coast-liveness-live-01"]["informative_enough_for_next_matched_metric"], False)

    def test_payload_loader_refuses_changed_source_blob(self):
        payload = json.dumps({
            "base_commit": "6968d45197c6a29e717a9281dcd050be1eed90c7",
            "sources": {name: "{}" for name in SOURCES},
        }).encode()
        with self.assertRaisesRegex(ValueError, "blob hash mismatch"):
            load_inputs_from_payload(payload)


if __name__ == "__main__":
    unittest.main()
