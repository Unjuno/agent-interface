#!/usr/bin/env python3
"""Mutation checks for the frozen V39 candidate-pair audit contract."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import audit


def fixture():
    typed = {}
    observed = {}
    rows = []
    for sequence, capture_ns, emit_ns, frame_hash in (
        (81, 1_000_000_000, 1_012_387_000, "a" * 64),
        (82, 1_342_409_000, 1_357_360_000, "b" * 64),
    ):
        event = {
            "sequence": sequence,
            "id": "cover-2",
            "capture_ns": capture_ns,
            "emit_ns": emit_ns,
            "frame_rgb_sha256": frame_hash,
            "signals": {"health": {"sequence": sequence, "value": 76}},
        }
        typed[("typed_observation", sequence)] = event
        observed[("observation", sequence)] = {
            "sequence": sequence,
            "id": "cover-2",
            "capture_ns": capture_ns,
            "emit_ns": emit_ns,
            "frame_rgb_sha256": frame_hash,
        }
        rows.append({
            "sequence": sequence,
            "id": "cover-2",
            "health": 76,
            "capture_ns": capture_ns,
            "emit_ns": emit_ns,
            "frame_rgb_sha256": frame_hash,
            "observation_exact_match": True,
        })
    pair = {
        "decision": "d2",
        "rows": rows,
        "capture_spacing_ms": 342.409,
        "emit_spacing_ms": 344.973,
        "capture_to_emit_ms": [12.387, 14.951],
        "distinct_frame_hashes": True,
    }
    return pair, {**typed, **observed}


class AuditV39PairTests(unittest.TestCase):
    def test_valid_frozen_pair(self):
        pair, indexed = fixture()
        audit.validate_v39_pair(pair, "d2", (81, 82), indexed)

    def test_rejects_substituted_sequences(self):
        pair, indexed = fixture()
        pair["rows"][0]["sequence"] = 79
        with self.assertRaises(AssertionError):
            audit.validate_v39_pair(pair, "d2", (81, 82), indexed)

    def test_rejects_mutated_derived_timing(self):
        pair, indexed = fixture()
        pair["capture_spacing_ms"] = 342.408
        with self.assertRaises(AssertionError):
            audit.validate_v39_pair(pair, "d2", (81, 82), indexed)

    def test_rejects_coherently_mutated_emissions(self):
        pair, indexed = fixture()
        for row in pair["rows"]:
            row["emit_ns"] += 50_000
        pair["capture_to_emit_ms"] = [12.437, 15.001]
        with self.assertRaises(AssertionError):
            audit.validate_v39_pair(pair, "d2", (81, 82), indexed)

    def test_accepts_the_complete_frozen_input_set(self):
        frozen = {name: f"hash-{name}" for name in audit.REQUIRED_INPUT_PATHS}
        inputs = {
            name: {"path": path, "sha256": frozen[name]}
            for name, path in audit.REQUIRED_INPUT_PATHS.items()
        }
        audit.validate_input_custody(inputs, frozen)

    def test_rejects_a_missing_frozen_input(self):
        frozen = {name: f"hash-{name}" for name in audit.REQUIRED_INPUT_PATHS}
        inputs = {
            name: {"path": path, "sha256": frozen[name]}
            for name, path in audit.REQUIRED_INPUT_PATHS.items()
            if name != "v39_report"
        }
        with self.assertRaises(AssertionError):
            audit.validate_input_custody(inputs, frozen)

    def test_rejects_a_missing_freeze_entry(self):
        frozen = {
            name: f"hash-{name}"
            for name in audit.REQUIRED_INPUT_PATHS
            if name != "v39_report"
        }
        inputs = {
            name: {"path": path, "sha256": f"hash-{name}"}
            for name, path in audit.REQUIRED_INPUT_PATHS.items()
        }
        with self.assertRaises(AssertionError):
            audit.validate_input_custody(inputs, frozen)

    def test_rejects_a_substituted_input_path(self):
        frozen = {name: f"hash-{name}" for name in audit.REQUIRED_INPUT_PATHS}
        inputs = {
            name: {"path": path, "sha256": frozen[name]}
            for name, path in audit.REQUIRED_INPUT_PATHS.items()
        }
        inputs["v39_report"]["path"] = "some/other/report.json"
        with self.assertRaises(AssertionError):
            audit.validate_input_custody(inputs, frozen)


if __name__ == "__main__":
    unittest.main()
