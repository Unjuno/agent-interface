from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = ROOT.parent / "needle_role_skill_lifecycle_4916_larger_rung_v1"
sys.path.insert(0, str(SOURCE_ROOT))
from lifecycle_corrected import ROLES, build_all, build_role, expected_rows, load_artifact, predict

REPO = ROOT.parents[2]
BUILDER = REPO / "research/needle_role_skill_reload_3780_v1/formal/seed-3788/builder"


class SuccessorLauncherContract(unittest.TestCase):
    def test_freeze_is_co_located_and_source_hashes_match(self):
        freeze_path = ROOT / "FREEZE.json"
        self.assertTrue(freeze_path.is_file())
        freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
        self.assertEqual(freeze["allocation"], "needle-role-skill-lifecycle-4916-larger-rung-20260928-03")
        for relative, expected in freeze["sources"].items():
            actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, relative)

    def test_each_entrypoint_binds_same_root_and_allocation(self):
        from launch_common import ALLOCATION, load_runner

        self.assertEqual(ALLOCATION, "needle-role-skill-lifecycle-4916-larger-rung-20260928-03")
        for module_name in ("construction_runner", "pilot_runner", "pilot_audit"):
            module = load_runner(module_name)
            self.assertEqual(module.ROOT, ROOT, module_name)
            self.assertEqual(module.ALLOCATION, ALLOCATION, module_name)
            self.assertTrue((module.ROOT / "FREEZE.json").is_file(), module_name)


class SuccessorConstruction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = BUILDER / "skill.json"
        cls.expected_path = BUILDER / "expected.json"
        cls.artifact, _ = load_artifact(cls.skill)
        cls.expected = expected_rows(cls.expected_path)

    def test_all_12288_retained_predictions(self):
        models = build_all(self.artifact)
        checked = 0
        for role in ROLES:
            fixture = self.expected["roles"][role]
            self.assertEqual([predict(models[role], row) for row in fixture["inputs"]], fixture["pred"], role)
            checked += len(fixture["inputs"])
        self.assertEqual(checked, 12288)

    def test_reload_and_reuse_exact_predictions(self):
        models = build_all(self.artifact)
        for index in (0, 37, 113, 199):
            role = ROLES[index % 3]
            row_index = (index * 37 + 11) % 4096
            row = self.expected["roles"][role]["inputs"][row_index]
            target = self.expected["roles"][role]["pred"][row_index]
            fresh, _ = load_artifact(self.skill)
            self.assertEqual(predict(build_role(fresh, role), row), target)
            self.assertEqual(predict(models[role], row), target)

    def test_corrupt_payload_is_rejected(self):
        obj = json.loads(self.skill.read_bytes())
        obj["tensors"]["A"]["head.bias"][0] += 0.25
        with tempfile.TemporaryDirectory() as tmp:
            altered = Path(tmp) / "corrupt.json"
            altered.write_text(json.dumps(obj), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "payload_digest"):
                load_artifact(altered)
        with self.assertRaisesRegex(ValueError, "unknown_role"):
            build_role(self.artifact, "Z")
