"""Fail-closed candidate contract for coherent refreshed game-state snapshots.

This qualifies snapshot coherence only. It does not establish changed-score
freshness, task effect, post-invalidation recovery, or permission to send input.
"""
from __future__ import annotations

import math
from numbers import Real
from typing import Any


def _unknown(reason: str) -> dict[str, Any]:
    return {
        "record": {"qualified": False, "reason": reason},
        "controller_reply": {"status": "UNKNOWN"},
    }


def qualify_state_snapshot(
    *,
    tic_before: int,
    tic_after: int,
    state_tic: int,
    game_variables: list[Real] | tuple[Real, ...],
    variable_names: list[str] | tuple[str, ...],
) -> dict[str, Any]:
    """Return a private snapshot record and status-only controller reply.

    A fresh snapshot may span multiple game tics. It must be strictly newer
    than the pre-update endpoint and agree with the acknowledged post-update
    endpoint. Invalid evidence returns UNKNOWN and carries no input authority.
    """
    tics = (tic_before, tic_after, state_tic)
    if any(isinstance(tic, bool) or not isinstance(tic, int) or tic < 0 for tic in tics):
        return _unknown("invalid_tic")
    if state_tic <= tic_before:
        return _unknown("snapshot_not_newer")
    if state_tic != tic_after:
        return _unknown("snapshot_tic_disagrees_with_endpoint")
    if not isinstance(game_variables, (list, tuple)) or not isinstance(variable_names, (list, tuple)):
        return _unknown("invalid_variable_payload")
    if len(game_variables) != len(variable_names):
        return _unknown("variable_count_mismatch")
    if any(not isinstance(name, str) or not name.strip() for name in variable_names):
        return _unknown("invalid_variable_name")
    if len(set(variable_names)) != len(variable_names):
        return _unknown("duplicate_variable_name")

    values: dict[str, float] = {}
    for name, value in zip(variable_names, game_variables):
        if isinstance(value, bool) or not isinstance(value, Real):
            return _unknown("invalid_game_variable")
        numeric_value = float(value)
        if not math.isfinite(numeric_value):
            return _unknown("invalid_game_variable")
        values[name] = numeric_value

    return {
        "record": {
            "qualified": True,
            "tic_before": tic_before,
            "tic_after": tic_after,
            "tic_delta": tic_after - tic_before,
            "state_tic": state_tic,
            "values": values,
            "grants_input_authority": False,
        },
        "controller_reply": {
            "status": "REFRESH_RETURNED_RUNTIME_QUALIFICATION_PENDING",
        },
    }
