"""Construction-only checks; never launches the formal publisher/readers."""
import copy
import json
import unittest

from protocol import (
    NEW_GENERATION,
    OLD_GENERATION,
    PHASES,
    READER_COUNT,
    candidate_from,
    payload_digest,
    proposal_disposition,
    validate_package,
)


def tiny_package():
    package = {
        "schema": "unjuno.role-skill.numeric-json.v1",
        "generation": OLD_GENERATION,
        "provenance": {"allocation": "fixture", "predecessor_issue": 3780, "seed": 3788},
        "tensors": {"A": {"bias": [0.0]}, "B": {"adapter": [[1.0]]}},
    }
    package["payload_sha256"] = payload_digest(package)
    return package


class ProtocolConstructionTests(unittest.TestCase):
    def test_fixed_roster_and_finite_schedule(self):
        self.assertEqual(READER_COUNT, 4)
        self.assertEqual(len(PHASES), 7)
        self.assertEqual(len(PHASES), len(set(PHASES)))

    def test_candidate_changes_generation_but_preserves_tensor_bytes(self):
        old = tiny_package()
        new = candidate_from(old)
        self.assertTrue(validate_package(old))
        self.assertTrue(validate_package(new))
        self.assertEqual(old["generation"], OLD_GENERATION)
        self.assertEqual(new["generation"], NEW_GENERATION)
        self.assertEqual(old["tensors"], new["tensors"])
        self.assertNotEqual(old["payload_sha256"], new["payload_sha256"])

    def test_invalid_digest_is_rejected_without_mutating_active(self):
        active = tiny_package()
        before = json.dumps(active, sort_keys=True, separators=(",", ":"))
        invalid = candidate_from(active)
        invalid["payload_sha256"] = "0" * 64
        self.assertFalse(validate_package(invalid))
        self.assertEqual(before, json.dumps(active, sort_keys=True, separators=(",", ":")))

    def test_generation_admission_fails_closed_after_switch(self):
        self.assertEqual(proposal_disposition(OLD_GENERATION, OLD_GENERATION), "ELIGIBLE_PROPOSAL_ONLY")
        self.assertEqual(proposal_disposition(OLD_GENERATION, NEW_GENERATION), "YIELD_STALE_GENERATION")
        self.assertEqual(proposal_disposition(NEW_GENERATION, NEW_GENERATION), "ELIGIBLE_PROPOSAL_ONLY")

    def test_corrupted_generation_cannot_keep_old_digest(self):
        package = tiny_package()
        changed = copy.deepcopy(package)
        changed["generation"] = NEW_GENERATION
        self.assertFalse(validate_package(changed))


if __name__ == "__main__":
    unittest.main()

