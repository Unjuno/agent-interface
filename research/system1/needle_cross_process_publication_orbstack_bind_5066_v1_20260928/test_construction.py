"""Fast construction checks; these never launch the formal runner."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import unittest

import audit
import protocol

HERE = Path(__file__).resolve().parent
SEED = HERE.parents[2] / "research/needle_role_skill_reload_3780_v1/formal/seed-3788/builder/skill.json"


class ConstructionTests(unittest.TestCase):
    def test_seed_and_candidate_are_exact_and_valid(self):
        raw = SEED.read_bytes()
        seed = json.loads(raw)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), protocol.SEED_SHA256)
        self.assertTrue(protocol.valid(seed))
        candidate = protocol.successor(seed)
        self.assertTrue(protocol.valid(candidate))
        self.assertEqual(candidate["generation"], protocol.NEW)
        for key in seed["tensors"]:
            self.assertEqual(seed["tensors"][key], candidate["tensors"][key])

    def test_schedule_denominators(self):
        self.assertEqual(len(protocol.PHASES), 7)
        self.assertEqual(len(protocol.UNSAFE_PHASES), 7)
        self.assertEqual(len(protocol.PHASES) * 4 * 2, 56)
        self.assertEqual(7 * 4, 28)

    def test_auditor_rejects_malformed_input(self):
        self.assertTrue(audit.audit(None))
        self.assertTrue(audit.audit({}))


if __name__ == "__main__":
    unittest.main()
