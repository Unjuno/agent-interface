"""Source-lineage validation before public CLI dispatch."""
from __future__ import annotations
import hashlib, json
from typing import Any, Mapping

SCHEMA = "agent-interface/lineage-dispatch-result-v1"


def _canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def program_digest(program: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canon(program)).hexdigest()


def receipt_digest(receipt: Mapping[str, Any]) -> str:
    fields = {key: receipt[key] for key in (
        "receipt_id", "role", "currentness", "point", "observation_seq",
        "binding_revision", "source_receipt_id"
    )}
    return hashlib.sha256(_canon(fields)).hexdigest()


def sidecar_digest(sidecar: Mapping[str, Any]) -> str:
    fields = {key: sidecar[key] for key in (
        "program_digest", "evidence_receipt_digest", "role", "currentness",
        "point", "observation_seq", "binding_revision"
    )}
    return hashlib.sha256(_canon(fields)).hexdigest()


def _pointer_point(program: Mapping[str, Any]) -> list[int]:
    points = [(op["x"], op["y"]) for op in program.get("ops", [])
              if op.get("op") == "pointer_move"]
    if len(points) != 1:
        raise ValueError("PROGRAM_POINTER_SHAPE_UNSUPPORTED")
    return list(points[0])


def validate_lineage(program: Mapping[str, Any], receipt: Mapping[str, Any],
                     sidecar: Mapping[str, Any]) -> None:
    if receipt.get("digest") != receipt_digest(receipt):
        raise ValueError("EVIDENCE_RECEIPT_DIGEST_MISMATCH")
    if sidecar.get("digest") != sidecar_digest(sidecar):
        raise ValueError("SIDECAR_DIGEST_MISMATCH")
    if sidecar.get("program_digest") != program_digest(program):
        raise ValueError("PROGRAM_DIGEST_MISMATCH")
    if sidecar.get("evidence_receipt_digest") != receipt.get("digest"):
        raise ValueError("EVIDENCE_DIGEST_MISMATCH")
    for key in ("role", "currentness", "point", "observation_seq", "binding_revision"):
        if sidecar.get(key) != receipt.get(key):
            raise ValueError("SIDECAR_RECEIPT_MISMATCH")
    if receipt.get("role") != "ADMISSION_DEPENDENCY" or receipt.get("currentness") != "CURRENT":
        raise ValueError("LINEAGE_NOT_CURRENT_ADMISSION")
    if program.get("source") != {
        "observation_seq": receipt.get("observation_seq"),
        "binding_revision": receipt.get("binding_revision"),
    }:
        raise ValueError("PROGRAM_SOURCE_MISMATCH")
    if _pointer_point(program) != list(receipt["point"]):
        raise ValueError("PROGRAM_POINT_MISMATCH")


def dispatch_with_lineage(
    program: dict[str, Any],
    targets: Mapping[str, int],
    receipt: Mapping[str, Any],
    sidecar: Mapping[str, Any],
    *,
    current_observation_seq: int,
    current_binding_revision: int,
    display_name: str | None = None,
    capture_directory: str | None = None,
    dispatch_fn=None,
) -> dict[str, Any]:
    try:
        validate_lineage(program, receipt, sidecar)
    except (KeyError, TypeError, ValueError) as error:
        return {"schema": SCHEMA, "status": "lineage_rejected", "error": str(error)}
    if dispatch_fn is None:
        from .api import dispatch
        dispatch_fn = dispatch
    result = dispatch_fn(
        program, targets,
        current_observation_seq=current_observation_seq,
        current_binding_revision=current_binding_revision,
        display_name=display_name,
        capture_directory=capture_directory,
    )
    return {"schema": SCHEMA, "status": "delegated", "cli_result": result}
