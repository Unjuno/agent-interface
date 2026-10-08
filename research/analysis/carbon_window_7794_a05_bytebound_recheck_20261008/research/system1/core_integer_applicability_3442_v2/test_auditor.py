from __future__ import annotations

import copy
import hashlib
import json
import unittest

from research.system1.core_integer_applicability_3442_v2.auditor import (
    audit_row,
    audit_rows,
    verify_corruption_controls,
)


MAIN_SHA = "a" * 40
SOURCE_SHA = "b" * 64


def _valid_program(value: object) -> dict[str, object]:
    return {
        "schema": "agent-interface/program-v1",
        "program_id": "integer-boundary-study",
        "source": {"observation_seq": value, "binding_revision": 1},
        "authority": {"lease_id": "fixture-lease", "expires_at_ns": 1000},
        "terminal": {"release_all_required": True},
        "ops": [
            {"op": "activate", "target": "fixture-window", "timeout_ms": 10},
            {"op": "pointer_move", "frame": "screen_physical_px", "x": 0, "y": 0},
            {"op": "scroll", "dx": 0, "dy": 0},
            {"op": "observe", "frame": "screen_physical_px", "x": 0, "y": 0, "w": 1, "h": 1},
            {"op": "wait_update", "timeout_ms": 10},
            {"op": "release_all"},
        ],
    }


def _record(value: object, *, kind: str, accepted: bool) -> dict[str, object]:
    program = _valid_program(value)
    raw = json.dumps(program, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return {
        "case_id": f"source.observation_seq/{kind}/direct",
        "field": "source.observation_seq",
        "kind": kind,
        "mode": "direct",
        "candidate": value,
        "candidate_type": type(value).__name__,
        "observed_value": program["source"]["observation_seq"],
        "observed_type": type(program["source"]["observation_seq"]).__name__,
        "main_sha": MAIN_SHA,
        "contract_source_sha256": SOURCE_SHA,
        "input_program": program,
        "input_program_sha256": hashlib.sha256(raw).hexdigest(),
        "admission_inputs": {
            "now_ns": 0,
            "current_observation_seq": value if type(value) is int else 1,
            "current_binding_revision": 1,
        },
        "validation": {
            "accepted": accepted,
            "error": None if accepted else "source.observation_seq must be int",
            "operation_index": None,
            "returned_same_object": accepted,
        },
        "admission": {
            "accepted": accepted,
            "error": None if accepted else "INVALID_PROGRAM",
            "required_capabilities": [
                "capture.frame",
                "clock.monotonic",
                "display.geometry",
                "event.feedback",
                "input.pointer",
                "input.release_all",
                "input.scroll",
                "window.activate",
            ] if accepted else [],
        },
        "admission_inputs": {
            "now_ns": 0,
            "current_observation_seq": value if type(value) is int else 1,
            "current_binding_revision": 1,
        },
        "wire_json": None,
        "wire_sha256": None,
    }


_FIELDS = {
    "source.observation_seq": (("source", "observation_seq"), 0, 2**63 - 1, "source.observation_seq", None),
    "source.binding_revision": (("source", "binding_revision"), 0, 2**63 - 1, "source.binding_revision", None),
    "authority.expires_at_ns": (("authority", "expires_at_ns"), 1, 2**63 - 1, "authority.expires_at_ns", None),
    "activate.timeout_ms": (("ops", 0, "timeout_ms"), 0, 2_000, "activate timeout_ms", 0),
    "pointer_move.x": (("ops", 1, "x"), -1_000_000, 1_000_000, "pointer x", 1),
    "pointer_move.y": (("ops", 1, "y"), -1_000_000, 1_000_000, "pointer y", 1),
    "scroll.dx": (("ops", 2, "dx"), -100_000, 100_000, "scroll dx", 2),
    "scroll.dy": (("ops", 2, "dy"), -100_000, 100_000, "scroll dy", 2),
    "observe.x": (("ops", 3, "x"), -1_000_000, 1_000_000, "observe x", 3),
    "observe.y": (("ops", 3, "y"), -1_000_000, 1_000_000, "observe y", 3),
    "observe.w": (("ops", 3, "w"), 1, 1_000_000, "observe w", 3),
    "observe.h": (("ops", 3, "h"), 1, 1_000_000, "observe h", 3),
    "wait_update.timeout_ms": (("ops", 4, "timeout_ms"), 0, 60_000, "wait_update.timeout_ms", 4),
}
_KINDS = (
    "lo", "lo_plus_one", "lo_plus_two", "hi_minus_one", "hi", "mid",
    "below", "above", "bool_false", "bool_true", "float_lo", "float_mid",
    "float_hi", "str_lo", "null",
)


def _directed_value(kind: str, lo: int, hi: int) -> object:
    mid = (lo + hi) // 2
    values = {
        "lo": lo,
        "lo_plus_one": lo + 1,
        "lo_plus_two": lo + 2,
        "hi_minus_one": hi - 1,
        "hi": hi,
        "mid": mid,
        "below": lo - 1,
        "above": hi + 1,
        "bool_false": False,
        "bool_true": True,
        "float_lo": float(lo),
        "float_mid": float(mid),
        "float_hi": float(hi),
        "str_lo": str(lo),
        "null": None,
    }
    return values[kind]


def _synthetic_matrix() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    required = [
        "capture.frame", "clock.monotonic", "display.geometry", "event.feedback",
        "input.pointer", "input.release_all", "input.scroll", "window.activate",
    ]
    for field, (path, lo, hi, error_name, op_index) in _FIELDS.items():
        for kind in _KINDS:
            candidate = _directed_value(kind, lo, hi)
            accepted = type(candidate) is int and lo <= candidate <= hi
            for mode in ("direct", "json_roundtrip"):
                program = _valid_program(1)
                parent = program
                for key in path[:-1]:
                    parent = parent[key]
                parent[path[-1]] = candidate
                wire = None
                wire_sha = None
                if mode == "json_roundtrip":
                    wire = json.dumps(program, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
                    program = json.loads(wire)
                    wire_sha = hashlib.sha256(wire.encode()).hexdigest()
                raw = json.dumps(program, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
                actual = program
                for key in path:
                    actual = actual[key]
                error = None
                if not accepted:
                    error = (
                        f"{error_name} out of range [{lo}, {hi}]"
                        if type(candidate) is int
                        else f"{error_name} must be int"
                    )
                seq = program["source"]["observation_seq"]
                binding = program["source"]["binding_revision"]
                rows.append(
                    {
                        "case_id": f"{field}/{kind}/{mode}",
                        "field": field,
                        "kind": kind,
                        "mode": mode,
                        "candidate": candidate,
                        "candidate_type": type(candidate).__name__,
                        "observed_value": actual,
                        "observed_type": type(actual).__name__,
                        "main_sha": MAIN_SHA,
                        "contract_source_sha256": SOURCE_SHA,
                        "input_program": program,
                        "input_program_sha256": hashlib.sha256(raw).hexdigest(),
                        "wire_json": wire,
                        "wire_sha256": wire_sha,
                        "admission_inputs": {
                            "now_ns": 0,
                            "current_observation_seq": seq if type(seq) is int else 1,
                            "current_binding_revision": binding if type(binding) is int else 1,
                        },
                        "validation": {
                            "accepted": accepted,
                            "error": error,
                            "operation_index": op_index,
                            "returned_same_object": accepted,
                        },
                        "admission": {
                            "accepted": accepted,
                            "error": None if accepted else "INVALID_PROGRAM",
                            "required_capabilities": required if accepted else [],
                        },
                    }
                )
    return rows


class RawOnlyAuditorTests(unittest.TestCase):
    def test_accepts_in_range_exact_integer_raw_row(self) -> None:
        self.assertEqual(audit_row(_record(0, kind="lo", accepted=True), MAIN_SHA, SOURCE_SHA), [])

    def test_accepts_boolean_refusal_even_when_false_compares_equal_to_zero(self) -> None:
        row = _record(False, kind="bool_false", accepted=False)
        self.assertEqual(audit_row(row, MAIN_SHA, SOURCE_SHA), [])

    def test_rejects_candidate_program_disagreement(self) -> None:
        row = _record(0, kind="lo", accepted=True)
        row["candidate"] = 1
        self.assertTrue(audit_row(row, MAIN_SHA, SOURCE_SHA))

    def test_rejects_mutated_program_bytes_even_when_outcome_is_unchanged(self) -> None:
        row = _record(0, kind="lo", accepted=True)
        changed = copy.deepcopy(row["input_program"])
        changed["ops"][0]["timeout_ms"] = 11
        row["input_program"] = changed
        self.assertTrue(audit_row(row, MAIN_SHA, SOURCE_SHA))

    def test_full_synthetic_matrix_and_ten_corruption_controls(self) -> None:
        rows = _synthetic_matrix()
        report = audit_rows(rows, MAIN_SHA, SOURCE_SHA)
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["rows"], 390)
        self.assertEqual(report["accepted"], 156)
        self.assertEqual(report["refused"], 234)
        self.assertEqual(report["per_mode"]["direct"], {"rows": 195, "accepted": 78, "refused": 117})
        controls = verify_corruption_controls(rows, MAIN_SHA, SOURCE_SHA)
        self.assertEqual(len(controls), 10)
        self.assertTrue(all(control["rejected"] for control in controls), controls)


if __name__ == "__main__":
    unittest.main()
