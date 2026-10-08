from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.core_v1.contract import (
    KNOWN_CAPABILITIES,
    ContractError,
    admit_program,
    capability_manifest,
    validate_program,
)


FIELD_SPECS: dict[str, tuple[tuple[str | int, ...], int, int]] = {
    "source.observation_seq": (("source", "observation_seq"), 0, 2**63 - 1),
    "source.binding_revision": (("source", "binding_revision"), 0, 2**63 - 1),
    "authority.expires_at_ns": (("authority", "expires_at_ns"), 1, 2**63 - 1),
    "activate.timeout_ms": (("ops", 0, "timeout_ms"), 0, 2_000),
    "pointer_move.x": (("ops", 1, "x"), -1_000_000, 1_000_000),
    "pointer_move.y": (("ops", 1, "y"), -1_000_000, 1_000_000),
    "scroll.dx": (("ops", 2, "dx"), -100_000, 100_000),
    "scroll.dy": (("ops", 2, "dy"), -100_000, 100_000),
    "observe.x": (("ops", 3, "x"), -1_000_000, 1_000_000),
    "observe.y": (("ops", 3, "y"), -1_000_000, 1_000_000),
    "observe.w": (("ops", 3, "w"), 1, 1_000_000),
    "observe.h": (("ops", 3, "h"), 1, 1_000_000),
    "wait_update.timeout_ms": (("ops", 4, "timeout_ms"), 0, 60_000),
}
CASE_KINDS = (
    "lo",
    "lo_plus_one",
    "lo_plus_two",
    "hi_minus_one",
    "hi",
    "mid",
    "below",
    "above",
    "bool_false",
    "bool_true",
    "float_lo",
    "float_mid",
    "float_hi",
    "str_lo",
    "null",
)
MODES = ("direct", "json_roundtrip")
FIXTURE_MANIFEST = capability_manifest(
    "integer-boundary-fixture",
    "macos",
    "inert",
    KNOWN_CAPABILITIES,
)


def _case_values(lo: int, hi: int) -> dict[str, Any]:
    mid = (lo + hi) // 2
    return {
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


def build_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for field, (_location, lo, hi) in FIELD_SPECS.items():
        for kind, value in _case_values(lo, hi).items():
            for mode in MODES:
                cases.append(
                    {
                        "case_id": f"{field}/{kind}/{mode}",
                        "field": field,
                        "kind": kind,
                        "mode": mode,
                        "value": value,
                        "candidate_type": type(value).__name__,
                    }
                )
    return cases


def _set_path(value: dict[str, Any], path: tuple[str | int, ...], item: Any) -> None:
    parent: Any = value
    for key in path[:-1]:
        parent = parent[key]
    parent[path[-1]] = item


def _get_path(value: dict[str, Any], path: tuple[str | int, ...]) -> Any:
    parent: Any = value
    for key in path:
        parent = parent[key]
    return parent


def build_program(field: str | None = None, value: Any = None) -> dict[str, Any]:
    program: dict[str, Any] = {
        "schema": "agent-interface/program-v1",
        "program_id": "integer-boundary-study",
        "source": {"observation_seq": 1, "binding_revision": 1},
        "authority": {"lease_id": "fixture-lease", "expires_at_ns": 1000},
        "terminal": {"release_all_required": True},
        "ops": [
            {"op": "activate", "target": "fixture-window", "timeout_ms": 10},
            {
                "op": "pointer_move",
                "frame": "screen_physical_px",
                "x": 0,
                "y": 0,
            },
            {"op": "scroll", "dx": 0, "dy": 0},
            {
                "op": "observe",
                "frame": "screen_physical_px",
                "x": 0,
                "y": 0,
                "w": 1,
                "h": 1,
            },
            {"op": "wait_update", "timeout_ms": 10},
            {"op": "release_all"},
        ],
    }
    if field is not None:
        _set_path(program, FIELD_SPECS[field][0], value)
    return program


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def run_case(
    case: dict[str, Any],
    *,
    main_sha: str,
    source_sha256: str,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    candidate = case["value"]
    program = build_program(case["field"], candidate)
    wire_json: str | None = None
    wire_sha256: str | None = None
    if case["mode"] == "json_roundtrip":
        wire_bytes = _canonical_json(program)
        wire_json = wire_bytes.decode("utf-8")
        wire_sha256 = hashlib.sha256(wire_bytes).hexdigest()
        program = json.loads(wire_json)

    input_bytes = _canonical_json(program)
    field_path, _lo, _hi = FIELD_SPECS[case["field"]]
    observed_value = _get_path(program, field_path)
    validation: dict[str, Any]
    try:
        returned = validate_program(program)
        validation = {
            "accepted": True,
            "error": None,
            "operation_index": None,
            "returned_same_object": returned is program,
        }
    except ContractError as error:
        validation = {
            "accepted": False,
            "error": str(error),
            "operation_index": getattr(error, "operation_index", None),
            "returned_same_object": False,
        }

    admission_inputs = {
        "now_ns": 0,
        "current_observation_seq": (
            program["source"]["observation_seq"]
            if type(program["source"]["observation_seq"]) is int
            else 1
        ),
        "current_binding_revision": (
            program["source"]["binding_revision"]
            if type(program["source"]["binding_revision"]) is int
            else 1
        ),
    }
    admission = admit_program(
        program,
        manifest if manifest is not None else FIXTURE_MANIFEST,
        **admission_inputs,
    )
    return {
        "case_id": case["case_id"],
        "field": case["field"],
        "kind": case["kind"],
        "mode": case["mode"],
        "candidate": candidate,
        "candidate_type": type(candidate).__name__,
        "observed_value": observed_value,
        "observed_type": type(observed_value).__name__,
        "main_sha": main_sha,
        "contract_source_sha256": source_sha256,
        "input_program": program,
        "input_program_sha256": hashlib.sha256(input_bytes).hexdigest(),
        "wire_json": wire_json,
        "wire_sha256": wire_sha256,
        "admission_inputs": admission_inputs,
        "validation": validation,
        "admission": {
            "accepted": admission.accepted,
            "error": admission.error,
            "required_capabilities": list(admission.required_capabilities),
        },
    }


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the frozen integer-boundary case matrix once.")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--main-sha", required=True)
    args = parser.parse_args(argv)

    contract_path = _repo_root() / "runtime/core_v1/contract.py"
    source_sha256 = hashlib.sha256(contract_path.read_bytes()).hexdigest()
    rows = [
        run_case(case, main_sha=args.main_sha, source_sha256=source_sha256)
        for case in build_cases()
    ]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )
    print(f"rows={len(rows)} raw_sha256={hashlib.sha256(args.out.read_bytes()).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
