"""Stage-0 evidence-contract tests. No model fit or optimizer is invoked."""
from __future__ import annotations

import json
import hashlib
import unittest
from pathlib import Path

from fixture_builder import build_fixture
from raw_auditor import audit_bytes


def parsed_fixture() -> dict[str, object]:
    return json.loads(build_fixture())


def encode(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode() + b"\n"


class Stage0Tests(unittest.TestCase):
    def test_frozen_source_identities(self) -> None:
        root = Path(__file__).parent
        freeze_bytes = (root / "FREEZE.json").read_bytes()
        freeze = json.loads(freeze_bytes)
        sidecar = (root / "FREEZE.sha256").read_bytes()
        self.assertEqual(sidecar, hashlib.sha256(freeze_bytes).hexdigest().encode() + b"\n")
        for name, expected in freeze["source_sha256"].items():
            actual = hashlib.sha256((root / name).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, name)

    def test_positive_covers_three_synthetic_seeds_and_four_arms(self) -> None:
        result = audit_bytes(build_fixture())
        self.assertTrue(result["accepted"], result["errors"])
        self.assertEqual(result["seeds"], 3)
        self.assertEqual(result["arm_rows"], 12)
        self.assertEqual(result["base_schedule_rows"], 1200)
        self.assertEqual(result["optimizer_updates"], 0)

    def test_missing_schedule_digest_rejected(self) -> None:
        raw = parsed_fixture()
        del raw["runs"][0]["dataset_sha256"]["base_row_indices"]
        self.assertFalse(audit_bytes(encode(raw))["accepted"])

    def test_extra_digest_key_rejected(self) -> None:
        raw = parsed_fixture()
        raw["runs"][0]["dataset_sha256"]["unregistered"] = "0" * 64
        self.assertFalse(audit_bytes(encode(raw))["accepted"])

    def test_reordered_indices_rejected(self) -> None:
        raw = parsed_fixture()
        indices = raw["runs"][0]["base_row_indices"]
        indices[0], indices[1] = indices[1], indices[0]
        self.assertFalse(audit_bytes(encode(raw))["accepted"])

    def test_duplicate_index_mutation_rejected(self) -> None:
        raw = parsed_fixture()
        indices = raw["runs"][0]["base_row_indices"]
        indices[0] = indices[1]
        self.assertFalse(audit_bytes(encode(raw))["accepted"])

    def test_single_mutated_index_rejected(self) -> None:
        raw = parsed_fixture()
        raw["runs"][0]["base_row_indices"][0] = (raw["runs"][0]["base_row_indices"][0] + 1) % 256
        self.assertFalse(audit_bytes(encode(raw))["accepted"])

    def test_digest_mismatch_rejected(self) -> None:
        raw = parsed_fixture()
        raw["runs"][0]["dataset_sha256"]["base_row_indices"] = "0" * 64
        self.assertFalse(audit_bytes(encode(raw))["accepted"])

    def test_noncanonical_json_rejected(self) -> None:
        raw = build_fixture()
        pretty = json.dumps(json.loads(raw), indent=2, sort_keys=True).encode() + b"\n"
        self.assertFalse(audit_bytes(pretty)["accepted"])

    def test_duplicate_json_key_rejected(self) -> None:
        raw = build_fixture().replace(b'"fit_invocations":0', b'"fit_invocations":0,"fit_invocations":0', 1)
        self.assertFalse(audit_bytes(raw)["accepted"])

    def test_inconsistent_arm_seed_identity_rejected(self) -> None:
        raw = parsed_fixture()
        raw["runs"][0]["arms"][0]["arm"] = "ROUTED_SEPARATE_SKILLS"
        self.assertFalse(audit_bytes(encode(raw))["accepted"])

    def test_nonzero_optimizer_count_rejected(self) -> None:
        raw = parsed_fixture()
        raw["optimizer_updates"] = 1
        self.assertFalse(audit_bytes(encode(raw))["accepted"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
