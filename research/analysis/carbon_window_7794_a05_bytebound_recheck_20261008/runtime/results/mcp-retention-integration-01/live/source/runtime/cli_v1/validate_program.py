"""Display-free static validation; never open a backend or dispatch input.

Run with ``python -m runtime.cli_v1.validate_program --program program.json``.
Exit 0 means static validity only, 1 means invalid program, and 2 means the
input file could not be decoded/loaded. Existing runtime admission is unchanged.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.core_v1.contract import ContractError, required_capabilities, validate_program
from runtime.core_v1.sequence import expand_key_repeats, expand_text_gaps

SCHEMA = "agent-interface/static-program-validation-v1"
MAX_INPUT_BYTES = 1_048_576


def _result(status: str, valid: bool | None, **fields: Any) -> dict[str, Any]:
    return {
        "schema": SCHEMA, "status": status, "static_valid": valid,
        "side_effect_authority": False, "runtime_admission": "not_evaluated",
        "backend_checked": False, "task_success": None, **fields,
    }


def _detail(error: Exception) -> str:
    """Do not return arbitrary operation names or caller-provided key names."""
    text = str(error)
    if text.startswith("unsupported op "):
        text = "unsupported operation"
    elif text.startswith("key ") and text.endswith(" already held"):
        text = "key already held"
    elif text.startswith("key ") and text.endswith(" released while not held"):
        text = "key released while not held"
    return text[:256]


def inspect_program(program: Any) -> dict[str, Any]:
    """Validate a JSON-like program using the SAME expansion order as dispatch.

    Unknown fields retain the existing core semantics. This is not a strict
    original-JSON parser, a capability probe, a lease check or an input permit.
    The caller's object is not modified. No program or input text is returned.
    """
    if not isinstance(program, dict):
        return _result("invalid", False, error="PROGRAM_NOT_OBJECT",
                       detail="program must be object", detail_source="program_validation")
    candidate = deepcopy(program)
    operations = candidate.get("ops")
    sources = None
    compilation = None
    # Preserve dispatch's gap-before-repeat precedence, including mixed programs.
    if isinstance(operations, list):
        if any(isinstance(op, dict) and "gap_ms" in op for op in operations):
            compilation = "bounded_text_gap"
            try:
                candidate["ops"], sources = expand_text_gaps(operations)
            except ValueError as error:
                return _result("invalid", False, error="INVALID_TEXT_GAP",
                               detail=_detail(error), detail_source="sequence_expansion")
        elif any(isinstance(op, dict) and "repeat" in op for op in operations):
            compilation = "bounded_key_repeat"
            try:
                candidate["ops"] = expand_key_repeats(operations, max_ops=128)
            except ValueError as error:
                return _result("invalid", False, error="INVALID_KEY_REPEAT",
                               detail=_detail(error), detail_source="sequence_expansion")
            sources = [{"source_operation_index": index}
                       for index, op in enumerate(operations)
                       for _ in range(op.get("repeat", 1))]
    try:
        validate_program(candidate)
    except ContractError as error:
        location: dict[str, Any] = {}
        index = getattr(error, "operation_index", None)
        if type(index) is int and 0 <= index < 128:
            location["expanded_operation_index"] = index
            location["source_operation_index"] = (
                sources[index]["source_operation_index"] if sources is not None else index
            )
        return _result("invalid", False, error="INVALID_PROGRAM",
                       detail=_detail(error), detail_source="program_validation",
                       compilation=compilation, **location)
    except (TypeError, ValueError):
        # Some legacy membership checks raise for an invalid JSON field type.
        return _result("invalid", False, error="INVALID_PROGRAM",
                       detail="program contains an invalid field type",
                       detail_source="program_validation", compilation=compilation)
    return _result("valid", True, source_operation_count=len(operations),
                   expanded_operation_count=len(candidate["ops"]),
                   required_capabilities=list(required_capabilities(candidate)),
                   compilation=compilation)


def inspect_file(path: Path) -> dict[str, Any]:
    """Inspect a bounded local UTF-8 JSON file; paths/content are not echoed."""
    try:
        with path.open("rb") as stream:
            raw = stream.read(MAX_INPUT_BYTES + 1)
    except OSError:
        return _result("input_error", None, error="INPUT_UNREADABLE")
    if len(raw) > MAX_INPUT_BYTES:
        return _result("input_error", None, error="INPUT_TOO_LARGE")
    identity = hashlib.sha256(raw).hexdigest()
    try:
        program = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as error:
        return _result("input_error", None, error="INVALID_JSON",
                       line=error.lineno, column=error.colno, input_sha256=identity)
    except (UnicodeError, ValueError, RecursionError):
        return _result("input_error", None, error="INVALID_JSON_ENCODING_OR_LIMIT",
                       input_sha256=identity)
    try:
        report = inspect_program(program)
    except RecursionError:
        return _result("input_error", None, error="INPUT_NESTING_LIMIT", input_sha256=identity)
    report["input_sha256"] = identity
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--program", type=Path, required=True, help="local UTF-8 JSON program")
    args = parser.parse_args(argv)
    report = inspect_file(args.program)
    print(json.dumps(report, ensure_ascii=True, sort_keys=True))
    return {"valid": 0, "invalid": 1, "input_error": 2}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
