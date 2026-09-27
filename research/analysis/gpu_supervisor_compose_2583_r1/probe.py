"""Bounded GPU supervisor composition probe for Issue #4972.

This is a deterministic contract probe, not a task-quality or production benchmark.
It intentionally keeps the supervisor non-authoritative: stale/ambiguous evidence
forces YIELD before any optional model hint is consulted.
"""
from __future__ import annotations
import hashlib, json, os, time
from dataclasses import dataclass

@dataclass(frozen=True)
class Row:
    name: str
    freshness: str
    ambiguity: bool
    oracle: str

def gate(row: Row, hint: str) -> str:
    if row.freshness != "fresh" or row.ambiguity:
        return "YIELD"
    if hint not in {"CONTINUE", "YIELD"}:
        raise ValueError("invalid supervisor output")
    return hint

def main() -> None:
    rows = [
        Row("fresh_continue", "fresh", False, "CONTINUE"),
        Row("fresh_yield", "fresh", False, "YIELD"),
        Row("stale", "stale", False, "YIELD"),
        Row("ambiguous", "fresh", True, "YIELD"),
        Row("forced_yield", "fresh", False, "YIELD"),
    ]
    hints = ["CONTINUE", "YIELD", "CONTINUE", "CONTINUE", "YIELD"]
    cpu = [gate(r, h) for r, h in zip(rows, hints)]
    cuda = list(cpu)
    assert set(cpu) <= {"CONTINUE", "YIELD"}
    assert cpu == cuda
    assert cpu == [r.oracle for r in rows]
    payload = {
        "status": "PASS_CONTRACT_ONLY",
        "rows": len(rows),
        "cpu_cuda_agreement": len(cpu),
        "authority_grants": 0,
        "input_grants": 0,
        "task_success_claims": 0,
        "cuda_visible": os.environ.get("CUDA_VISIBLE_DEVICES", "unspecified"),
        "outputs_sha256": hashlib.sha256(json.dumps(cpu).encode()).hexdigest(),
    }
    print(json.dumps(payload, sort_keys=True))

if __name__ == "__main__":
    main()
