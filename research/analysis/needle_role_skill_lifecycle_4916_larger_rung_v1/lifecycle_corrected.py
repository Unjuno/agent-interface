"""Corrected candidate scorer from merged first-rung evidence."""

from __future__ import annotations

import math
import sys
from pathlib import Path

V2 = Path(__file__).resolve().parents[1] / "needle_role_skill_lifecycle_4916_v2"
sys.path.insert(0, str(V2))
from lifecycle import ROLES, _f32, _linear, build_all, build_role, expected_rows, load_artifact  # noqa: E402


def predict(model: tuple, row: list[float]) -> int:
    ew, eb, hw, hb, a, b = model
    x = tuple(_f32(item) for item in row)
    hidden = tuple(_f32(math.tanh(item)) for item in _linear(x, ew, eb))
    logits = list(_linear(hidden, hw, hb))
    if a is not None:
        rank = _linear(hidden, [list(col) for col in zip(*a)], [0.0, 0.0])
        delta = _linear(rank, [list(col) for col in zip(*b)], [0.0] * 4)
        logits = [_f32(base + _f32(change / 2.0)) for base, change in zip(logits, delta)]
    return max(range(len(logits)), key=logits.__getitem__)
