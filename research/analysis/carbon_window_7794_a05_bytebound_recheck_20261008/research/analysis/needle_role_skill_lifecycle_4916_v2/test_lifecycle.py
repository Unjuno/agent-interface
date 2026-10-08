from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from lifecycle import build_all, build_role, expected_rows, load_artifact, predict
from audit_result import audit_mutations

ROOT = Path(__file__).parent
INPUT = Path(os.environ.get("ROLE_SKILL_DATA_DIR", ROOT.parents[1] / "needle_role_skill_reload_3780_v1/formal/seed-3788/builder"))


class LifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = INPUT / "skill.json"
        cls.expected = expected_rows(INPUT / "expected.json")
        cls.artifact, _ = load_artifact(cls.skill)

    def test_full_retained_prediction_parity(self):
        models = build_all(self.artifact)
        for role in ("A", "B", "C"):
            fixture = self.expected["roles"][role]
            actual = [predict(models[role], row) for row in fixture["inputs"]]
            self.assertEqual(actual, fixture["pred"], role)

    def test_reload_and_reuse_emit_identical_predictions(self):
        models = build_all(self.artifact)
        for i in range(1000):
            role = ("A", "B", "C")[i % 3]
            row_index = (i * 37 + 11) % 4096
            row = self.expected["roles"][role]["inputs"][row_index]
            expected = self.expected["roles"][role]["pred"][row_index]
            fresh, _ = load_artifact(self.skill)
            self.assertEqual(predict(build_role(fresh, role), row), expected)
            self.assertEqual(predict(models[role], row), expected)

    def test_payload_corruption_rejected(self):
        obj = json.loads(self.skill.read_text())
        obj["tensors"]["A"]["head.bias"][0] += 0.25
        with tempfile.TemporaryDirectory() as tmp:
            altered = Path(tmp) / "altered.json"
            altered.write_text(json.dumps(obj))
            with self.assertRaisesRegex(ValueError, "payload_digest"):
                load_artifact(altered)

    def test_wrong_generation_and_unknown_role_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            obj = json.loads(self.skill.read_text())
            obj["generation"] += 1
            from lifecycle import canonical_payload
            obj["payload_sha256"] = __import__("hashlib").sha256(canonical_payload(obj)).hexdigest()
            altered = Path(tmp) / "generation.json"
            altered.write_text(json.dumps(obj))
            with self.assertRaisesRegex(ValueError, "schema_or_generation"):
                load_artifact(altered)
        with self.assertRaisesRegex(ValueError, "unknown_role"):
            build_role(self.artifact, "Z")

    def test_independent_auditor_rejects_declared_corruptions(self):
        role = "A"
        row_index = 11
        schedule = [{"role": role, "index": row_index, "expected": self.expected["roles"][role]["pred"][row_index]}]
        raw = {"blocks": [{"arms": {"LOAD_ONCE_REUSE": {"predictions": [schedule[0]["expected"]]}}}]}
        with tempfile.TemporaryDirectory() as tmp:
            raw_path = Path(tmp) / "raw.json"
            raw_path.write_text(json.dumps(raw))
            controls = audit_mutations(self.skill, raw_path, schedule)
        self.assertEqual((controls["rejected"], controls["total"]), (2, 2))


if __name__ == "__main__":
    unittest.main()
