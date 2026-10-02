"""Behavior-first tests for the finite symmetry experiment candidate."""
from __future__ import annotations

import pathlib
import json
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import candidate


class TypedPermutationTests(unittest.TestCase):
    def test_cli_writes_machine_readable_result_to_explicit_path(self):
        with tempfile.TemporaryDirectory() as temp:
            output = pathlib.Path(temp) / "candidate.json"
            completed = subprocess.run(
                [sys.executable, "-B", str(pathlib.Path(candidate.__file__).resolve()), "--output", str(output)],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["schema"], "issue6251-symmetry-t0-host-v1")

    def test_verifier_renaming_preserves_a_replica_symmetric_state(self):
        state = {
            "lease_holder": "verifier_a",
            "replyers": ["verifier_a"],
            "generation": 0,
            "commit_by": None,
            "effect_target": "record_x",
            "receipt_target": None,
        }
        renamed = candidate.permute_state(
            state, {"verifier_a": "verifier_b", "verifier_b": "verifier_a"}
        )
        world = candidate.world()

        self.assertEqual(candidate.typed_key(state, world), candidate.typed_key(renamed, world))

    def test_requester_identity_is_not_quotiented_with_verifier_identity(self):
        requester_commit = {
            "lease_holder": None,
            "replyers": [],
            "generation": 0,
            "commit_by": "requester",
            "effect_target": "record_x",
            "receipt_target": None,
        }
        verifier_commit = {**requester_commit, "commit_by": "verifier_a"}

        self.assertNotEqual(
            candidate.typed_key(requester_commit, candidate.world()),
            candidate.typed_key(verifier_commit, candidate.world()),
        )

    def test_identity_breakers_fall_back_to_named_state_enumeration(self):
        for broken in (
            {"fixed_verifier": "verifier_a"},
            {"named_property_actor": "verifier_a"},
            {"omit_effect_target": True},
        ):
            with self.subTest(broken=broken):
                result = candidate.reduce_world({**candidate.world(), **broken})
                self.assertTrue(result["fallback_to_named_states"])

    def test_full_candidate_preserves_counterexamples_and_reduces_symmetric_states(self):
        result = candidate.run()
        symmetric = result["symmetric"]
        self.assertGreater(symmetric["full_state_count"], symmetric["quotient_state_count"])
        self.assertEqual(symmetric["unsafe_exists_full"], symmetric["unsafe_exists_quotient"])
        self.assertTrue(symmetric["all_counterexamples_expand"])
        self.assertTrue(result["mutation_controls_rejected"])


if __name__ == "__main__":
    unittest.main()
