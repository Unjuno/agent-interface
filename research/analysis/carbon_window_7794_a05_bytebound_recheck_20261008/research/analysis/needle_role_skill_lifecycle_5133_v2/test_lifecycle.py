from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

from lifecycle_corrected import ROLES, build_all, build_role, expected_rows, load_artifact, predict
from audit_raw import oracle

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
BUILDER = REPO / "research/needle_role_skill_reload_3780_v1/formal/seed-3788/builder"


class LifecycleConstruction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = BUILDER / "skill.json"
        cls.expected_path = BUILDER / "expected.json"
        cls.artifact, _ = load_artifact(cls.skill)
        cls.expected = expected_rows(cls.expected_path)

    def test_frozen_input_hashes(self):
        self.assertEqual(hashlib.sha256(self.skill.read_bytes()).hexdigest(), "2e7bff5a2c6ffd35935c5e3c88d08cb686fb736d332c8d5cdb24bb1b67dc873a")
        self.assertEqual(hashlib.sha256(self.expected_path.read_bytes()).hexdigest(), "5baca462abbcdd561dba4c790775a589f91a0fa15453e2f3e6c3bc74fb1b6f61")

    def test_freeze_source_and_reference_hashes(self):
        freeze = json.loads((ROOT / "FREEZE.json").read_bytes())
        for name, digest in freeze["sources"].items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), digest, name)
        for name, path in freeze["reference_sources"].items():
            self.assertEqual(hashlib.sha256((REPO / path).read_bytes()).hexdigest(), freeze["reference_sources_sha256"][name], path)

    def test_frozen_commands_use_host_paths_and_pinned_offline_image(self):
        freeze = json.loads((ROOT / "FREEZE.json").read_bytes())
        self.assertEqual(freeze["base_main"], "3007e03481d545eb9a92b8cec07c8c4201bd3728")
        self.assertEqual(freeze["container"]["image_id"], "sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419")
        for command in freeze["commands"].values():
            self.assertIn("--pull=never", command)
            self.assertIn("--network none", command)
            self.assertIn(freeze["container"]["image_id"], command)
            self.assertNotIn("/private/tmp", command)
            self.assertNotIn("--privileged", command)
        if os.name == "nt":
            for host_path in freeze["host_paths"].values():
                self.assertTrue(Path(host_path.replace("/", "\\")).exists(), host_path)
        else:
            commands = " ".join(freeze["commands"].values())
            for host_path in freeze["host_paths"].values():
                self.assertTrue(host_path.startswith("C:/"), host_path)
                self.assertIn(host_path, commands)

    def test_all_12288_retained_predictions(self):
        models = build_all(self.artifact)
        count = 0
        for role in ROLES:
            fixture = self.expected["roles"][role]
            self.assertEqual([predict(models[role], row) for row in fixture["inputs"]], fixture["pred"], role)
            count += len(fixture["inputs"])
        self.assertEqual(count, 12288)

    def test_independent_oracle_reconstructs_all_12288(self):
        for role in ROLES:
            fixture = self.expected["roles"][role]
            for index, row in enumerate(fixture["inputs"]):
                self.assertEqual(oracle(self.artifact["tensors"][role], role, row), fixture["pred"][index], (role, index))

    def test_reload_and_reuse_selected_role_match(self):
        models = build_all(self.artifact)
        for i in (0, 37, 113, 199):
            role = ROLES[i % len(ROLES)]
            index = (i * 37 + 11) % 4096
            row = self.expected["roles"][role]["inputs"][index]
            target = self.expected["roles"][role]["pred"][index]
            fresh, _ = load_artifact(self.skill)
            self.assertEqual(predict(build_role(fresh, role), row), target)
            self.assertEqual(predict(models[role], row), target)

    def test_corrupt_payload_and_unknown_role_rejected(self):
        obj = json.loads(self.skill.read_bytes())
        obj["tensors"]["A"]["head.bias"][0] += 0.25
        with tempfile.TemporaryDirectory() as tmp:
            changed = Path(tmp) / "corrupt.json"
            changed.write_text(json.dumps(obj), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "payload_digest"):
                load_artifact(changed)
        with self.assertRaisesRegex(ValueError, "unknown_role"):
            build_role(self.artifact, "Z")


if __name__ == "__main__":
    unittest.main(verbosity=2)
