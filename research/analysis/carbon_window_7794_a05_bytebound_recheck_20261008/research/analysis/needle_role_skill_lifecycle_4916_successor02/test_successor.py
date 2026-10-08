from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from audit_successor import NEW_ALLOCATION, OLD_ALLOCATION, V1, build_auditor_source

ROOT = Path(__file__).parent
REPO = ROOT.parents[2]
BUILDER = REPO / "research/needle_role_skill_reload_3780_v1/formal/seed-3788/builder"


class SuccessorFreezeTests(unittest.TestCase):
    def test_repository_relative_mount_resolves_frozen_test_fallback(self):
        test_file = V1 / "test_lifecycle.py"
        resolved = test_file.parent.parents[1] / "needle_role_skill_reload_3780_v1/formal/seed-3788/builder"
        self.assertEqual(resolved, BUILDER)
        self.assertTrue((resolved / "skill.json").is_file())

    def test_predecessor_source_and_inputs_match_immutable_freeze(self):
        freeze = json.loads((V1 / "FREEZE.json").read_bytes())
        for name, expected in freeze["sources"].items():
            self.assertEqual(hashlib.sha256((V1 / name).read_bytes()).hexdigest(), expected, name)
        self.assertEqual(hashlib.sha256((BUILDER / "skill.json").read_bytes()).hexdigest(), freeze["inputs"]["skill_sha256"])
        self.assertEqual(hashlib.sha256((BUILDER / "expected.json").read_bytes()).hexdigest(), freeze["inputs"]["expected_sha256"])

    def test_auditor_changes_only_one_allocation_literal(self):
        before = (V1 / "audit_result.py").read_bytes()
        after = build_auditor_source()
        self.assertEqual(before.count(OLD_ALLOCATION.encode()), 1)
        self.assertEqual(before.count(NEW_ALLOCATION.encode()), 0)
        self.assertEqual(after.count(OLD_ALLOCATION.encode()), 0)
        self.assertEqual(after.count(NEW_ALLOCATION.encode()), 1)
        self.assertEqual(after, before.replace(OLD_ALLOCATION.encode(), NEW_ALLOCATION.encode(), 1))

    def test_successor_wrappers_compile(self):
        for filename in ("run_successor.py", "audit_successor.py", "construction_successor.py"):
            source = (ROOT / filename).read_bytes()
            compile(source, filename, "exec")


if __name__ == "__main__":
    unittest.main()
