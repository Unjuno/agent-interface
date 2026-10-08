import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
BUILDER = PACKAGE / "build_fixture.py"
CANDIDATE = PACKAGE / "candidate" / "candidate.py"
AUDITOR = PACKAGE / "auditor" / "audit.py"
MUTATIONS = PACKAGE / "auditor" / "audit_controls.py"


def invoke(*args):
    return subprocess.run(
        [sys.executable, *map(str, args)],
        capture_output=True,
        text=True,
        check=False,
    )


class AllocationProtocolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.fixture_root = self.root / "fixture"
        built = invoke(BUILDER, "--output-root", self.fixture_root)
        self.assertEqual(0, built.returncode, built.stderr)
        self.public_path = self.fixture_root / "candidate-input" / "public.json"
        self.truth_path = self.fixture_root / "auditor-input" / "truth.json"
        self.candidate_path = self.root / "candidate.json"
        candidate = invoke(CANDIDATE, "--input", self.public_path, "--output", self.candidate_path)
        self.assertEqual(0, candidate.returncode, candidate.stderr)

    def tearDown(self):
        self.temp.cleanup()

    def test_fixture_separates_four_conflicting_truth_pairs_from_six_controls(self):
        public = json.loads(self.public_path.read_text())
        truth = json.loads(self.truth_path.read_text())

        self.assertEqual(14, len(public["rows"]))
        self.assertEqual(14, len(truth["rows"]))
        self.assertEqual(4, len(truth["equivalence_pairs"]))
        for pair in truth["equivalence_pairs"]:
            left, right = pair["ordinals"]
            self.assertEqual(public["rows"][left], public["rows"][right])
            self.assertNotEqual(
                truth["rows"][left]["correct_return_label"],
                truth["rows"][right]["correct_return_label"],
            )

    def test_candidate_input_directory_contains_no_auditor_truth_file(self):
        self.assertEqual(["public.json"], sorted(path.name for path in self.public_path.parent.iterdir()))
        self.assertFalse((self.public_path.parent / "truth.json").exists())

    def test_independent_auditor_accepts_the_frozen_candidate_packet(self):
        audit_path = self.root / "audit.json"
        result = invoke(
            AUDITOR,
            "--public",
            self.public_path,
            "--truth",
            self.truth_path,
            "--candidate",
            self.candidate_path,
            "--output",
            audit_path,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        audit = json.loads(audit_path.read_text())
        self.assertEqual("PASS_METHOD_SCOPED", audit["disposition"])
        self.assertEqual(14, audit["rows_reconstructed"])
        self.assertEqual([], audit["errors"])

    def test_independent_auditor_rejects_all_eight_frozen_packet_mutations(self):
        controls_path = self.root / "mutation-controls.json"
        result = invoke(
            MUTATIONS,
            "--public",
            self.public_path,
            "--truth",
            self.truth_path,
            "--candidate",
            self.candidate_path,
            "--output",
            controls_path,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        controls = json.loads(controls_path.read_text())
        self.assertEqual(8, controls["mutations_attempted"])
        self.assertEqual(8, controls["mutations_rejected"])
        self.assertEqual([], controls["accepted_mutations"])


if __name__ == "__main__":
    unittest.main()
