"""Dependency-free lifecycle probe for the retained numeric role-skill JSON."""

from __future__ import annotations

import hashlib
import json
import math
import struct
from pathlib import Path

SCHEMA = "unjuno.role-skill.numeric-json.v1"
ROLES = ("A", "B", "C")
SHAPES = {
    "enc.0.weight": (16, 8), "enc.0.bias": (16,),
    "head.weight": (4, 16), "head.bias": (4,),
    "core.enc.0.weight": (16, 8), "core.enc.0.bias": (16,),
    "core.head.weight": (4, 16), "core.head.bias": (4,),
    "a": (16, 2), "b": (2, 4),
}
KEYS = {
    "A": {"enc.0.weight", "enc.0.bias", "head.weight", "head.bias"},
    "B": {"core.enc.0.weight", "core.enc.0.bias", "core.head.weight", "core.head.bias", "a", "b"},
    "C": {"core.enc.0.weight", "core.enc.0.bias", "core.head.weight", "core.head.bias", "a", "b"},
}


def _shape(value: object) -> tuple[int, ...]:
    if not isinstance(value, list):
        return ()
    if not value:
        return (0,)
    child = _shape(value[0])
    if any(_shape(item) != child for item in value):
        raise ValueError("ragged_tensor")
    return (len(value), *child)


def canonical_payload(obj: dict) -> bytes:
    unsigned = dict(obj)
    unsigned.pop("payload_sha256", None)
    return json.dumps(unsigned, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def load_artifact(path: str | Path) -> tuple[dict, int]:
    raw = Path(path).read_bytes()
    obj = json.loads(raw)
    if obj.get("schema") != SCHEMA or obj.get("generation") != 3788:
        raise ValueError("schema_or_generation")
    if set(obj.get("tensors", {})) != set(ROLES):
        raise ValueError("role_set")
    digest = obj.get("payload_sha256")
    if not isinstance(digest, str) or hashlib.sha256(canonical_payload(obj)).hexdigest() != digest:
        raise ValueError("payload_digest")
    for role in ROLES:
        tensors = obj["tensors"][role]
        if set(tensors) != KEYS[role]:
            raise ValueError("tensor_keys")
        for name, value in tensors.items():
            if _shape(value) != SHAPES[name]:
                raise ValueError("tensor_shape")
            if not _finite_bounded(value):
                raise ValueError("tensor_value")
    return obj, len(raw)


def _finite_bounded(value: object) -> bool:
    if isinstance(value, list):
        return all(_finite_bounded(item) for item in value)
    return type(value) in (int, float) and math.isfinite(value) and abs(value) < 1e6


def _f32(value: float) -> float:
    return struct.unpack("!f", struct.pack("!f", value))[0]


def _linear(x: tuple[float, ...], weight: list, bias: list) -> tuple[float, ...]:
    outputs = []
    for i, row in enumerate(weight):
        acc = 0.0
        for left, right in zip(row, x):
            acc = _f32(acc + _f32(left * right))
        outputs.append(_f32(acc + _f32(bias[i])))
    return tuple(outputs)


def build_role(artifact: dict, role: str) -> tuple:
    if role not in ROLES:
        raise ValueError("unknown_role")
    t = artifact["tensors"][role]
    if role == "A":
        return (t["enc.0.weight"], t["enc.0.bias"], t["head.weight"], t["head.bias"], None, None)
    return (t["core.enc.0.weight"], t["core.enc.0.bias"], t["core.head.weight"], t["core.head.bias"], t["a"], t["b"])


def build_all(artifact: dict) -> dict[str, tuple]:
    return {role: build_role(artifact, role) for role in ROLES}


def predict(model: tuple, row: list[float]) -> int:
    ew, eb, hw, hb, a, b = model
    x = tuple(_f32(item) for item in row)
    hidden = tuple(_f32(math.tanh(item)) for item in _linear(x, ew, eb))
    logits = list(_linear(hidden, hw, hb))
    if a is not None:
        rank = _linear(hidden, [list(col) for col in zip(*a)], [0.0, 0.0])
        delta = _linear(rank, b, [0.0, 0.0, 0.0, 0.0])
        logits = [_f32(base + _f32(change / 2.0)) for base, change in zip(logits, delta)]
    return max(range(len(logits)), key=logits.__getitem__)


def expected_rows(path: str | Path) -> dict:
    obj = json.loads(Path(path).read_bytes())
    if set(obj["roles"]) != set(ROLES) or any(len(obj["roles"][r]["inputs"]) != 4096 for r in ROLES):
        raise ValueError("expected_fixture_shape")
    return obj
