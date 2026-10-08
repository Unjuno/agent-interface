"""Corruption controls for the independent v13 boundary raw auditor."""
from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("boundary_audit", HERE / "audit_controlled_boundary_v13.py")
AUDIT = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(AUDIT)


class RawAuditMutationTests(unittest.TestCase):
    def setUp(self):
        self.result = {
            "controller_decided_ns": 199,
            "capture_ns": 200,
            "observation_sequence": 2,
            "delta_ns": -1,
            "logged_before_result": True,
            "guard_state": "INPUT_ACTIVE",
            "logical_authority_still_active": True,
            "error": AUDIT.EXPECTED_ERROR,
        }
        self.source_event = {
            "sequence": 2, "capture_ns": 200,
            "typed_ready_ns": 250, "emit_ns": 275,
        }
        self.row = {
            "schema": "running-action-clock-check-v1",
            "capture_ns": 200, "controller_decided_ns": 199,
            "comparison_delta_ns": -1, "sequence": 2,
            "observation_event": {
                "sequence": 2, "capture_ns": 200,
                "typed_ready_ns": 250, "emit_ns": 275,
            },
            "calibration": None, "calibration_sha256": None,
            "offset_lower_ns": None, "host_clock": None, "runtime_clock": None,
        }

    def assert_mutation_rejected(self, target, path, value):
        result, row, source = map(copy.deepcopy, (self.result, self.row, self.source_event))
        current = {"result": result, "row": row, "source": source}[target]
        parent = current
        for key in path[:-1]:
            parent = parent[key]
        parent[path[-1]] = value
        self.assertTrue(AUDIT.validate_case(result, row, source, -1, AUDIT.EXPECTED_ERROR))

    def test_positive_boundary_row_reconciles(self):
        self.assertEqual([], AUDIT.validate_case(
            self.result, self.row, self.source_event, -1, AUDIT.EXPECTED_ERROR))

    def test_rejects_twelve_effective_mutations(self):
        cases = [
            ("result", ("controller_decided_ns",), 198),
            ("row", ("controller_decided_ns",), 198),
            ("result", ("delta_ns",), 0),
            ("row", ("comparison_delta_ns",), 0),
            ("result", ("capture_ns",), 201),
            ("row", ("sequence",), 3),
            ("row", ("observation_event", "typed_ready_ns"), 251),
            ("row", ("observation_event", "emit_ns"), 276),
            ("result", ("error",), None),
            ("result", ("guard_state",), "CANCEL_REQUIRED"),
            ("result", ("logical_authority_still_active",), False),
            ("result", ("logged_before_result",), False),
        ]
        for target, path, value in cases:
            with self.subTest(target=target, path=path):
                self.assert_mutation_rejected(target, path, value)


if __name__ == "__main__":
    unittest.main()
