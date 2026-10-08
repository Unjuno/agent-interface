"""Fresh digest-consistent schedule tampering controls for #5172 Stage 0."""
from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path

from audit_under_test import audit_bytes


ROOT = Path(__file__).parent
RAW_PATH = ROOT / "raw_fixture.json"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def changed_payload(change) -> bytes:
    value = json.loads(RAW_PATH.read_bytes())
    change(value)
    return canonical(value) + b"\n"


def mutate_base_value(value: dict) -> None:
    schedule = value["runs"][0]["base_row_indices"]
    schedule[0] = (schedule[0] + 1) % 256
    value["runs"][0]["dataset_sha256"]["base_row_indices"] = digest(schedule)


def reorder_base(value: dict) -> None:
    schedule = value["runs"][0]["base_row_indices"]
    schedule[0], schedule[1] = schedule[1], schedule[0]
    value["runs"][0]["dataset_sha256"]["base_row_indices"] = digest(schedule)


def mutate_arm_value(value: dict) -> None:
    arm = value["runs"][0]["arms"][0]
    arm["batch_row_indices"][0][0] = (arm["batch_row_indices"][0][0] + 1) % 16
    arm["schedule_sha256"] = digest(arm["batch_row_indices"])


def reorder_arm_schedule(value: dict) -> None:
    arm = value["runs"][0]["arms"][0]
    rows = arm["batch_row_indices"]
    rows[0], rows[8] = rows[8], rows[0]
    arm["schedule_sha256"] = digest(rows)


class DigestConsistentScheduleTests(unittest.TestCase):
    def test_frozen_sources_and_input_identity(self) -> None:
        freeze_bytes = (ROOT / "FREEZE.json").read_bytes()
        freeze = json.loads(freeze_bytes)
        self.assertEqual(
            (ROOT / "FREEZE.sha256").read_bytes(),
            hashlib.sha256(freeze_bytes).hexdigest().encode() + b"\n",
        )
        for name, expected in freeze["source_sha256"].items():
            actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, name)
        raw = RAW_PATH.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), freeze["raw_fixture_sha256"])

    def test_unchanged_fixture_is_accepted(self) -> None:
        result = audit_bytes(RAW_PATH.read_bytes())
        self.assertTrue(result["accepted"], result["errors"])
        self.assertEqual(result["errors"], [])

    def test_changed_base_index_rejected_even_with_recomputed_digest(self) -> None:
        result = audit_bytes(changed_payload(mutate_base_value))
        self.assertFalse(result["accepted"])
        self.assertIn("17:base_row_indices", result["errors"])

    def test_reordered_base_schedule_rejected_even_with_recomputed_digest(self) -> None:
        result = audit_bytes(changed_payload(reorder_base))
        self.assertFalse(result["accepted"])
        self.assertIn("17:base_row_indices", result["errors"])

    def test_changed_arm_schedule_rejected_even_with_recomputed_digest(self) -> None:
        result = audit_bytes(changed_payload(mutate_arm_value))
        self.assertFalse(result["accepted"])
        self.assertIn("17:SHARED_B_ONLY:batch_row_indices", result["errors"])

    def test_reordered_arm_schedule_rejected_even_with_recomputed_digest(self) -> None:
        result = audit_bytes(changed_payload(reorder_arm_schedule))
        self.assertFalse(result["accepted"])
        self.assertIn("17:SHARED_B_ONLY:batch_row_indices", result["errors"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
