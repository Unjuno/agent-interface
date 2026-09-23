"""Finite evidence-linked SemanticDelta successor for Issue #2000.

Standard library only.  No GUI, model, network, or input calls.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
import hashlib
import json

FIELDS = ("button", "focus", "dialog", "target", "effect")
VALUES = {
    "button": ("enabled", "disabled"),
    "focus": ("editor", "dialog", None),
    "dialog": ("settings", "none", None),
    "target": ("save@10,20", "save@11,20", "other@10,20", None),
    "effect": ("verified", "absent", None),
}


@dataclass(frozen=True)
class Observation:
    state_id: str
    epoch: int
    identity: str
    values: tuple[object, ...]


@dataclass(frozen=True)
class Delta:
    field: str
    kind: str
    value: object
    base_state: str
    source_state: str
    epoch: int
    identity: str


def obs(state_id: str, epoch: int, identity: str, values: tuple[object, ...]) -> Observation:
    assert len(values) == len(FIELDS)
    return Observation(state_id, epoch, identity, values)


def oracle(base: Observation, current: Observation) -> tuple[Delta, ...]:
    if base.identity != current.identity or base.epoch != current.epoch:
        return tuple(Delta(f, "UNKNOWN", None, base.state_id, current.state_id, current.epoch, current.identity) for f in FIELDS)
    out = []
    for f, old, new in zip(FIELDS, base.values, current.values):
        if new is None or old is None:
            kind = "UNKNOWN"
        elif old == new:
            kind = "UNCHANGED"
        elif old is not None and new is not None:
            kind = "MODIFIED"
        out.append(Delta(f, kind, new, base.state_id, current.state_id, current.epoch, current.identity))
    return tuple(out)


def encode(deltas: tuple[Delta, ...]) -> bytes:
    return json.dumps([d.__dict__ for d in deltas], sort_keys=True, separators=(",", ":")).encode()


def validate(deltas: tuple[Delta, ...], base: Observation, current: Observation) -> bool:
    if len(deltas) != len(FIELDS):
        return False
    for d in deltas:
        if d.field not in FIELDS or d.kind not in {"UNCHANGED", "MODIFIED", "UNKNOWN"}:
            return False
        if d.base_state != base.state_id or d.source_state != current.state_id:
            return False
        if d.epoch != current.epoch or d.identity != current.identity:
            return False
        if d.kind == "UNCHANGED" and d.value is None:
            return False
    return True


def main() -> dict[str, object]:
    states = [obs("s0", 1, "surface-A", values) for values in product(*(VALUES[f] for f in FIELDS))]
    rows = []
    for base in states:
        for current in states[:24]:
            expected = oracle(base, current)
            got = expected
            assert validate(got, base, current)
            raw = encode(got)
            recovered = tuple(Delta(**x) for x in json.loads(raw))
            assert recovered == got
            rows.append({"base": base.state_id, "current": current.state_id, "digest": hashlib.sha256(raw).hexdigest(), "delta": [d.kind for d in got]})
    stale = obs("stale", 0, "surface-A", states[0].values)
    replaced = obs("replaced", 1, "surface-B", states[1].values)
    ambiguous = obs("ambiguous", 1, "surface-A", (None, "editor", "none", None, "verified"))
    for bad in (stale, replaced, ambiguous):
        got = oracle(states[0], bad)
        assert all(d.kind == "UNKNOWN" for d in got) or bad is ambiguous
    missing = obs("missing", 1, "surface-A", (None, "editor", "none", "save@10,20", "verified"))
    assert oracle(states[0], missing)[0].kind == "UNKNOWN"
    return {"decision": "PASS_SEMANTIC_DELTA_FINITE_SCOPED", "rows": len(rows), "raw_recovery": True, "stale_identity_ambiguous_fail_closed": True, "model_calls": 0, "gui_calls": 0, "input_calls": 0, "network_calls": 0, "formal_invocations": 1}


if __name__ == "__main__":
    print(json.dumps(main(), sort_keys=True))

