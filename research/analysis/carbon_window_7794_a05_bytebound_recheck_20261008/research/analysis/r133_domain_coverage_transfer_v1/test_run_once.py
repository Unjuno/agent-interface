import pathlib
import json
import subprocess
import unittest

from frozen_sources import SOURCES
from run_once import build_result


class RunnerTests(unittest.TestCase):
    def test_result_binds_candidate_hashes_to_frozen_source_manifest(self):
        root = pathlib.Path(__file__).resolve().parent
        repository = root.parents[2]
        sources = {
            name: subprocess.run(["git", "cat-file", "blob", blob], cwd=repository,
                                 check=True, capture_output=True).stdout.decode("utf-8")
            for name, (_, blob) in SOURCES.items()
        }
        payload = json.dumps({"base_commit": "6968d45197c6a29e717a9281dcd050be1eed90c7", "sources": sources}).encode()
        result = build_result(root, payload)
        self.assertEqual(result["decision"], "CANDIDATE_RECONSTRUCTED")
        self.assertEqual(result["source_provenance"]["base_commit"], "6968d45197c6a29e717a9281dcd050be1eed90c7")
        self.assertIn("candidate_sha256", result)
        self.assertIn("source_manifest_sha256", result)
        self.assertEqual(result["scope"], "posthoc transfer coverage only")


if __name__ == "__main__":
    unittest.main()
