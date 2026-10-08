import json
import pathlib
import unittest

from docker_handoff import build_payload, docker_command
from frozen_sources import load_inputs_from_payload


class DockerHandoffTests(unittest.TestCase):
    def test_container_command_attaches_stdin_for_frozen_payload(self):
        command = docker_command(pathlib.Path(__file__).resolve().parent)
        self.assertIn("-i", command)

    def test_host_handoff_exports_only_the_frozen_source_blobs(self):
        root = pathlib.Path(__file__).resolve().parents[2]
        payload = build_payload(root)
        inputs, provenance = load_inputs_from_payload(payload)
        envelope = json.loads(payload)
        self.assertEqual(set(envelope["sources"]), {"physical", "occupancy", "feedback", "calc"})
        self.assertEqual(inputs["physical"]["formal"]["actuations"], 6)
        self.assertEqual(provenance["base_commit"], "6968d45197c6a29e717a9281dcd050be1eed90c7")


if __name__ == "__main__":
    unittest.main()
