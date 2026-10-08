from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
from typing import Any


# Independent transcription of the numeric leaves and bounds in the frozen
# current-main source. This module intentionally imports neither study.py nor
# the runtime validator.
FIELD_SPECS: dict[str, tuple[tuple[str | int, ...], int, int, str, int | None]] = {
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
ACCEPT_KINDS = frozenset({"lo", "lo_plus_one", "lo_plus_two", "hi_minus_one", "hi", "mid"})
EXPECTED_CAPABILITIES = [
    "capture.frame",
    "clock.monotonic",
    "display.geometry",
    "event.feedback",
    "input.pointer",
    "input.release_all",
    "input.scroll",
    "window.activate",
]


def _value_for_kind(kind: str, lo: int, hi: int) -> Any:
    mid = (lo + hi) // 2
    values: dict[str, Any] = {
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


def _get_path(value: Any, path: tuple[str | int, ...]) -> Any:
    current = value
    for part in path:
        current = current[part]
    return current


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def audit_row(row: dict[str, Any], expected_main_sha: str, expected_source_sha256: str) -> list[str]:
    errors: list[str] = []
    field = row.get("field")
    kind = row.get("kind")
    mode = row.get("mode")
    case_id = row.get("case_id")

    if field not in FIELD_SPECS:
        return ["unknown field"]
    if kind not in CASE_KINDS:
        return ["unknown case kind"]
    if mode not in MODES:
        return ["unknown input mode"]
    if case_id != f"{field}/{kind}/{mode}":
        errors.append("case identity mismatch")

    path, lo, hi, error_name, operation_index = FIELD_SPECS[field]
    candidate = row.get("candidate")
    expected_candidate = _value_for_kind(kind, lo, hi)
    if type(candidate) is not type(expected_candidate) or candidate != expected_candidate:
        errors.append("candidate does not match the frozen directed value")
    expected_type = type(expected_candidate).__name__
    if row.get("candidate_type") != expected_type:
        errors.append("candidate type label mismatch")

    program = row.get("input_program")
    if not isinstance(program, dict):
        errors.append("input program is not an object")
        program_value = object()
    else:
        try:
            program_value = _get_path(program, path)
        except (KeyError, IndexError, TypeError):
            program_value = object()
            errors.append("target field absent from input program")
        if type(program_value) is not type(candidate) or program_value != candidate:
            errors.append("candidate and input program disagree")
        try:
            actual_program_hash = hashlib.sha256(_canonical_json(program)).hexdigest()
            if row.get("input_program_sha256") != actual_program_hash:
                errors.append("input program hash mismatch")
        except (TypeError, ValueError):
            errors.append("input program cannot be canonicalized")

    if type(row.get("observed_value")) is not type(program_value) or row.get("observed_value") != program_value:
        errors.append("observed value differs from target in input program")
    if row.get("observed_type") != type(program_value).__name__:
        errors.append("observed type differs from target in input program")

    if row.get("main_sha") != expected_main_sha:
        errors.append("main source revision mismatch")
    if row.get("contract_source_sha256") != expected_source_sha256:
        errors.append("contract source hash mismatch")
    if not re.fullmatch(r"[0-9a-f]{40}", str(expected_main_sha)):
        errors.append("expected main SHA is malformed")
    if not re.fullmatch(r"[0-9a-f]{64}", str(expected_source_sha256)):
        errors.append("expected contract SHA-256 is malformed")

    expected_accept = type(expected_candidate) is int and lo <= expected_candidate <= hi
    validation = row.get("validation")
    admission = row.get("admission")
    if not isinstance(validation, dict) or not isinstance(admission, dict):
        return errors + ["validation or admission record missing"]
    if validation.get("accepted") is not expected_accept:
        errors.append("validator decision contradicts exact-int range oracle")
    if validation.get("operation_index") != operation_index:
        errors.append("operation index mismatch")
    if validation.get("returned_same_object") is not expected_accept:
        errors.append("validator object-identity receipt mismatch")
    if expected_accept:
        if validation.get("error") is not None:
            errors.append("accepted validator row carries an error")
    else:
        error = validation.get("error")
        if not isinstance(error, str):
            errors.append("refused validator row lacks exception text")
        elif type(expected_candidate) is int:
            if not error.startswith(f"{error_name} out of range [{lo}, {hi}]"):
                errors.append("range refusal text does not match frozen field bounds")
        elif error != f"{error_name} must be int":
            errors.append("type refusal text does not match exact-int gate")

    if admission.get("accepted") is not expected_accept:
        errors.append("admission decision differs from validator oracle")
    if expected_accept:
        if admission.get("error") is not None:
            errors.append("accepted admission carries an error")
        if admission.get("required_capabilities") != EXPECTED_CAPABILITIES:
            errors.append("accepted admission capability set mismatch")
    else:
        if admission.get("error") != "INVALID_PROGRAM":
            errors.append("invalid program was not refused as INVALID_PROGRAM")
        if admission.get("required_capabilities") != []:
            errors.append("invalid program unexpectedly produced required capabilities")

    admission_inputs = row.get("admission_inputs")
    if not isinstance(admission_inputs, dict):
        errors.append("admission inputs absent")
    elif isinstance(program, dict):
        src = program.get("source", {})
        expected_seq = src.get("observation_seq")
        expected_binding = src.get("binding_revision")
        if type(expected_seq) is not int:
            expected_seq = 1
        if type(expected_binding) is not int:
            expected_binding = 1
        if admission_inputs != {
            "now_ns": 0,
            "current_observation_seq": expected_seq,
            "current_binding_revision": expected_binding,
        }:
            errors.append("admission current-version controls do not match input")

    if mode == "json_roundtrip":
        wire = row.get("wire_json")
        if not isinstance(wire, str):
            errors.append("JSON-roundtrip mode lacks serialized wire bytes")
        else:
            try:
                if json.loads(wire) != program:
                    errors.append("JSON wire differs from received program")
                if row.get("wire_sha256") != hashlib.sha256(wire.encode()).hexdigest():
                    errors.append("JSON wire hash mismatch")
            except (json.JSONDecodeError, TypeError):
                errors.append("JSON wire is invalid")
    elif row.get("wire_json") is not None or row.get("wire_sha256") is not None:
        errors.append("direct mode unexpectedly carries a JSON wire")

    return errors


def audit_rows(
    rows: list[dict[str, Any]], expected_main_sha: str, expected_source_sha256: str
) -> dict[str, Any]:
    errors: list[str] = []
    expected_ids = {
        f"{field}/{kind}/{mode}"
        for field in FIELD_SPECS
        for kind in CASE_KINDS
        for mode in MODES
    }
    if len(rows) != len(expected_ids):
        errors.append(f"row denominator mismatch: expected {len(expected_ids)}, got {len(rows)}")
    by_id: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"row {index} is not an object")
            continue
        case_id = row.get("case_id")
        if case_id in by_id:
            errors.append(f"duplicate case: {case_id}")
        else:
            by_id[case_id] = row
        errors.extend(f"{case_id}: {error}" for error in audit_row(row, expected_main_sha, expected_source_sha256))

    if set(by_id) != expected_ids:
        errors.append("case coverage differs from the frozen matrix")

    for field in FIELD_SPECS:
        for kind in CASE_KINDS:
            direct_id = f"{field}/{kind}/direct"
            json_id = f"{field}/{kind}/json_roundtrip"
            direct = by_id.get(direct_id)
            roundtrip = by_id.get(json_id)
            if direct is None or roundtrip is None:
                continue
            for key in ("candidate", "candidate_type", "observed_value", "observed_type", "input_program", "validation", "admission", "admission_inputs"):
                left = direct.get(key)
                right = roundtrip.get(key)
                if type(left) is not type(right) or left != right:
                    errors.append(f"direct/JSON mismatch for {field}/{kind}: {key}")

    per_mode: dict[str, dict[str, int]] = {}
    for mode in MODES:
        mode_rows = [row for row in rows if isinstance(row, dict) and row.get("mode") == mode]
        per_mode[mode] = {
            "rows": len(mode_rows),
            "accepted": sum(row.get("validation", {}).get("accepted") is True for row in mode_rows),
            "refused": sum(row.get("validation", {}).get("accepted") is False for row in mode_rows),
        }
    return {
        "errors": errors,
        "rows": len(rows),
        "accepted": sum(row.get("validation", {}).get("accepted") is True for row in rows if isinstance(row, dict)),
        "refused": sum(row.get("validation", {}).get("accepted") is False for row in rows if isinstance(row, dict)),
        "per_mode": per_mode,
    }


def _control_mutations(rows: list[dict[str, Any]]) -> list[tuple[str, Any]]:
    def clone() -> list[dict[str, Any]]:
        return copy.deepcopy(rows)

    controls: list[tuple[str, Any]] = []

    missing = clone()
    missing.pop()
    controls.append(("missing_row", missing))

    duplicate = clone()
    duplicate.append(copy.deepcopy(duplicate[0]))
    controls.append(("duplicate_row", duplicate))

    changed_identity = clone()
    changed_identity[0]["case_id"] = "not-a-frozen-case"
    controls.append(("case_identity", changed_identity))

    changed_mode = clone()
    changed_mode[0]["mode"] = "invented_mode"
    controls.append(("mode", changed_mode))

    changed_value = clone()
    changed_value[0]["candidate"] += 1
    controls.append(("candidate_value", changed_value))

    changed_type = clone()
    changed_type[0]["candidate_type"] = "str"
    controls.append(("candidate_type", changed_type))

    changed_validation = clone()
    changed_validation[0]["validation"]["accepted"] = not changed_validation[0]["validation"]["accepted"]
    controls.append(("validation_outcome", changed_validation))

    changed_admission = clone()
    changed_admission[0]["admission"]["accepted"] = not changed_admission[0]["admission"]["accepted"]
    controls.append(("admission_outcome", changed_admission))

    changed_source = clone()
    changed_source[0]["contract_source_sha256"] = "0" * 64
    controls.append(("source_identity", changed_source))

    changed_program = clone()
    changed_program[0]["input_program"]["ops"][0]["timeout_ms"] += 1
    controls.append(("input_program_bytes", changed_program))
    return controls


def verify_corruption_controls(
    rows: list[dict[str, Any]], expected_main_sha: str, expected_source_sha256: str
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for name, mutated in _control_mutations(rows):
        rejected = bool(audit_rows(mutated, expected_main_sha, expected_source_sha256)["errors"])
        results.append({"name": name, "rejected": rejected})
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Independently audit the raw integer-boundary matrix.")
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--main-sha", required=True)
    parser.add_argument("--source-sha256", required=True)
    args = parser.parse_args(argv)

    raw_bytes = args.raw.read_bytes()
    rows = [json.loads(line) for line in raw_bytes.decode("utf-8").splitlines() if line]
    report = audit_rows(rows, args.main_sha, args.source_sha256)
    controls = verify_corruption_controls(rows, args.main_sha, args.source_sha256)
    report.update(
        {
            "schema_version": 1,
            "disposition": "PASS_CORE_INTEGER_BOUNDARY_SCOPED" if not report["errors"] else "FAIL_OR_HOLD",
            "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "auditor_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "corruption_controls": controls,
            "corruption_controls_passed": sum(row["rejected"] for row in controls),
            "corruption_controls_total": len(controls),
        }
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"disposition={report['disposition']} rows={report['rows']} "
        f"controls={report['corruption_controls_passed']}/{report['corruption_controls_total']} "
        f"raw_sha256={report['raw_sha256']}"
    )
    return 0 if not report["errors"] and report["corruption_controls_passed"] == report["corruption_controls_total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
