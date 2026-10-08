from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

import run

HERE = Path(__file__).resolve().parent
SEED = HERE.parents[1] / "needle_role_skill_reload_3780_v1/formal/seed-3788/builder/skill.json"


class PilotConstructionTests(unittest.TestCase):
    def test_exact_seed_and_one_generation_successor(self):
        raw = SEED.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         "2e7bff5a2c6ffd35935c5e3c88d08cb686fb736d332c8d5cdb24bb1b67dc873a")
        old, new = run.derive(json.loads(raw))
        old_obj, new_obj = json.loads(old), json.loads(new)
        self.assertEqual(old_obj["generation"], 3788)
        self.assertEqual(new_obj["generation"], 3789)
        self.assertEqual(new_obj["payload_sha256"], run.package_digest(new_obj))
        self.assertEqual(new_obj["provenance"]["allocation"], run.ALLOCATION)
        for key in old_obj.keys() - {"generation", "provenance", "payload_sha256"}:
            self.assertEqual(old_obj[key], new_obj[key])

    def test_container_boundary_is_explicit_and_networkless(self):
        source = (HERE / "launch.py").read_text()
        self.assertIn('"--network", "none"', source)
        self.assertIn('"--read-only"', source)
        self.assertIn('"--cap-drop", "ALL"', source)
        self.assertIn('"OBSTAC_CONSTRUCTION": "1"', source)
        self.assertIn("needle-publication-orbstack-boundary-20260930-01", source)

    def test_auditor_is_separate_and_imports_no_runner(self):
        audit = (HERE / "audit.py").read_text()
        self.assertNotIn("import run", audit)
        self.assertNotIn("import protocol", audit)
        self.assertIn("seed_candidate_reconstruction", audit)
        self.assertIn("atomic_held_old_bytes", audit)
        self.assertIn("unsafe_partial_prefix", audit)

    def test_frozen_plan_names_nonclaims(self):
        plan = (HERE / "PLAN.md").read_text()
        for term in ("**H.**", "**T.**", "**D.**", "**C.**", "**U.**",
                     "does not meet the formal", "does not release or replace allocation -03"):
            self.assertIn(term, plan)


if __name__ == "__main__":
    unittest.main()
