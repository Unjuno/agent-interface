"""Model-free bridge from a durable effect-owner receipt into typed outcome v3."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

from owner import read_execution_receipt, read_state_and_history

EXPECTED_V3_SHA256 = "4fd5a6001407b9e91ab3265aeca491643e035641f7926316ebf8835ba7b79449"
EXPECTED_V3_GIT_BLOB = "680b104b28ba37633ec1031eac41c1945eb3aed9"


def _dependency_path() -> Path:
    return Path(__file__).resolve().parents[1] / "effect_outcome_contract_v3" / "outcome.py"


def dependency_identity() -> dict:
    data = _dependency_path().read_bytes()
    sha256 = hashlib.sha256(data).hexdigest()
    git_blob = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
    return {"bytes": len(data), "sha256": sha256, "git_blob": git_blob}


def load_v3():
    identity = dependency_identity()
    if identity["sha256"] != EXPECTED_V3_SHA256 or identity["git_blob"] != EXPECTED_V3_GIT_BLOB:
        raise RuntimeError("effect outcome v3 dependency identity mismatch")
    name = "effect_outcome_contract_v3_dependency"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, _dependency_path())
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load effect outcome v3 dependency")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def classify_from_owner(
    *,
    db_path: Path,
    command_id: str,
    invariant_manifest,
    initial_state: str,
    intended_state: str,
    verification_evidence=(),
):
    """Use owner-persisted manifest identity; no free-form ExecutionBinding input exists."""
    v3 = load_v3()
    receipt = read_execution_receipt(db_path, command_id)
    current_state, raw_history = read_state_and_history(db_path, command_id)
    history = tuple(
        v3.Event(seq, v3.EventKind.EFFECT if kind == "effect" else v3.EventKind.COMPENSATION, value)
        for seq, kind, value in raw_history
    )
    binding = v3.ExecutionBinding(receipt.command_id, receipt.invariant_manifest_id)
    verification = None
    if any(kind == "compensation" for _, kind, _ in raw_history):
        verification = v3.VerificationReceipt(receipt.invariant_manifest_id, tuple(verification_evidence))
    return v3.reduce_outcome(
        operation_kind=v3.OperationKind.DIRECT,
        initial_state=initial_state,
        intended_state=intended_state,
        current_state=current_state,
        terminal_phase=v3.TerminalPhase.EFFECT_COMMITTED,
        events=history,
        invariant_manifest=invariant_manifest,
        execution_binding=binding,
        verification_receipt=verification,
    )
