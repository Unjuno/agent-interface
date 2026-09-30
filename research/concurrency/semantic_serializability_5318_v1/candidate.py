"""Finite synthetic proposal-concurrency experiment for Issue #5318."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Proposal:
    proposal_id: str
    operation: str
    key: str
    delta: int
    reads: tuple[str, ...]
    writes: tuple[str, ...]
    footprint_complete: bool = True
    commutativity_rule: str | None = None
    actual_reads: tuple[str, ...] = ()


def declared_conflicts(a: Proposal, b: Proposal) -> bool:
    if not a.footprint_complete or not b.footprint_complete:
        return False
    return bool(set(a.writes) & (set(b.reads) | set(b.writes)) or
                set(b.writes) & (set(a.reads) | set(a.writes)))


def oracle_step(state: dict[str, int], p: Proposal) -> None:
    if p.operation == "add":
        state[p.key] = state.get(p.key, 0) + p.delta
    elif p.operation == "copy":
        state[p.key] = state[p.actual_reads[0]]
    else:
        raise ValueError(p.operation)


def apply_order(initial: dict[str, int], order: tuple[Proposal, ...]) -> dict[str, int]:
    state = dict(initial)
    for p in order:
        oracle_step(state, p)
    return state


def legal_serial_outcomes(initial: dict[str, int], a: Proposal, b: Proposal):
    outcomes = []
    for order in ((a, b), (b, a)):
        outcomes.append(apply_order(initial, order))
    return outcomes


def run() -> dict:
    cases = [
        ("disjoint_commuting", {"x": 0, "y": 0},
         Proposal("a", "add", "x", 1, (), ("x",), commutativity_rule="integer-add-v1"),
         Proposal("b", "add", "y", 1, (), ("y",), commutativity_rule="integer-add-v1"), False),
        ("same_key_add", {"x": 0},
         Proposal("a", "add", "x", 1, (), ("x",), commutativity_rule="integer-add-v1"),
         Proposal("b", "add", "x", 2, (), ("x",), commutativity_rule="integer-add-v1"), False),
        ("read_write_order", {"x": 1, "y": 0},
         Proposal("a", "copy", "y", 0, ("x",), ("y",), actual_reads=("x",)),
         Proposal("b", "add", "x", 1, (), ("x",)), False),
        # Actual operation reads x, but its declared footprint omits x.
        ("hidden_read", {"x": 1, "y": 0},
         Proposal("a", "copy", "y", 0, (), ("y",), actual_reads=("x",)),
         Proposal("b", "add", "x", 1, (), ("x",)), False),
        ("unknown_footprint", {"x": 0, "y": 0},
         Proposal("a", "add", "x", 1, (), ("x",), footprint_complete=False),
         Proposal("b", "add", "y", 1, (), ("y",)), False),
    ]
    rows = []
    for name, initial, a, b, _ in cases:
        serial = legal_serial_outcomes(initial, a, b)
        actual_parallel = apply_order(initial, (b, a))
        semantically_legal = actual_parallel in serial
        declared_conflicting = declared_conflicts(a, b)
        unknown = not a.footprint_complete or not b.footprint_complete
        semantic_parallel = not declared_conflicting and not unknown
        raw_parallel = True
        actual_footprint_conflict = len({json.dumps(item, sort_keys=True) for item in serial}) > 1
        semantic_conflict = bool(semantic_parallel and actual_footprint_conflict)
        rows.append({
            "case": name, "initial": initial, "a": asdict(a), "b": asdict(b),
            "serial_outcomes": serial,
            "policies": {
                "RAW_COALESCE": {"decision": "PARALLEL", "serial_outcome_divergence": actual_footprint_conflict},
                "GLOBAL_SERIAL": {"decision": "SERIALIZE", "serial_outcome_divergence": False},
                "SEMANTIC_GATE": {"decision": "SERIALIZE" if declared_conflicting else ("UNCERTAIN" if unknown else "PARALLEL"),
                                   "serial_outcome_divergence": semantic_conflict},
            },
            "oracle": {"actual_read_write_conflict": not semantically_legal,
                       "declared_read_write_conflict": declared_conflicting,
                       "legal_serial_outcomes": serial,
                       "observed_concurrent_outcome": actual_parallel,
                       "concurrent_matches_serial": semantically_legal},
            "metrics": {"raw_parallel_pairs": int(raw_parallel),
                        "global_parallel_pairs": 0,
                        "semantic_parallel_pairs": int(semantic_parallel)},
        })
    return {"schema": "semantic-serializability-raw-v1", "allocation": "semantic-serializability-fsm-r0-20260930-01",
            "cases": rows, "authority_grants": 0, "external_effects": 0}


if __name__ == "__main__":
    import sys
    Path(sys.argv[1]).write_text(json.dumps(run(), sort_keys=True, separators=(",", ":")) + "\n")
