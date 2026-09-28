"""V2 raw audit: adds independently checked resets and A3→B1 geometry receipts.

The inherited event parser reconstructs model, image, input, release, score,
and timing evidence. This version additionally verifies every private reset
projection and the single between-task geometry witness for each arm. It does
not import the live runner, controller, or reset-witness implementation.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re

from raw_allocation_audit_v1 import (ARMS, HERE, LIVE, TASKS,
    RawAuditError, _load_evaluator, _validate_source_identity, reconstruct as reconstruct_v1)


RAW_FIELDS = {"schema", "allocation_id", "source_identity", "model_identity",
              "preflight_events", "arms", "transition_events"}
TASK_EXTRA = {"reset_event"}
TASKS_FIELDS_V2 = {"task_id", "layout", "route", "started_ns", "ended_ns",
    "observation_events", "model_call_events", "durable_call_ids", "input_events",
    "input_feedback_events", "release_events", "submission_events", "score_event",
    "repair_events", "reset_event"}
SNAPSHOT_FIELDS = {"tick", "paused", "tiles", "copper", "core_x", "core_y",
                   "source_item", "player_dead", "unit"}
TILE_FIELDS = {"x", "y", "block", "team", "rotation", "floor", "overlay"}
GUARD = {(x, y) for y in range(48, 56) for x in range(136, 150)}
TARGET = (137, 52)


def _finite_number(value: object) -> bool:
    # Integers are exact and finite regardless of magnitude. math.isfinite(int)
    # converts to float and can itself raise OverflowError on adversarial JSON.
    return (type(value) is int or
            (type(value) is float and math.isfinite(value)))


def _tile_map(snapshot: dict) -> dict[tuple[int, int], dict]:
    rows = snapshot.get("tiles")
    if type(rows) is not list or len(rows) != len(GUARD):
        raise RawAuditError("reset requires a full 112-tile guard projection")
    result = {}
    for row in rows:
        if type(row) is not dict or set(row) != TILE_FIELDS:
            raise RawAuditError("reset tile has incorrect raw fields")
        if type(row["x"]) is not int or type(row["y"]) is not int:
            raise RawAuditError("reset tile coordinates must be integers")
        xy = (row["x"], row["y"])
        if xy not in GUARD or xy in result:
            raise RawAuditError("reset tiles contain duplicate or out-of-guard coordinate")
        if (type(row["block"]) is not str or not row["block"]
                or type(row["floor"]) is not str or not row["floor"]
                or type(row["overlay"]) is not str or not row["overlay"]
                or type(row["team"]) is not int
                or (row["rotation"] is not None and
                    (type(row["rotation"]) is not int or row["rotation"] not in range(4)))):
            raise RawAuditError("reset tile has malformed engine fields")
        result[xy] = row
    if set(result) != GUARD:
        raise RawAuditError("reset tile coordinates do not cover guard")
    return result


def _verify_reset(before: object, after: object) -> None:
    if (type(before) is not dict or set(before) != SNAPSHOT_FIELDS
            or type(after) is not dict or set(after) != SNAPSHOT_FIELDS):
        raise RawAuditError("exact pre-task and reset snapshots required")
    original, reset = _tile_map(before), _tile_map(after)
    if before["paused"] is not True or after["paused"] is not True:
        raise RawAuditError("reset did not restore paused state")
    if before["player_dead"] is not False or after["player_dead"] is not False:
        raise RawAuditError("reset did not restore live-player state")
    if (type(after["unit"]) is not dict
            or set(after["unit"]) != {"x", "y", "type", "plans"}
            or type(after["unit"]["plans"]) is not int or after["unit"]["plans"] != 0
            or type(after["unit"]["type"]) is not str or not after["unit"]["type"]
            or any(not _finite_number(after["unit"][key])
                   for key in ("x", "y"))):
        raise RawAuditError("reset unit has plans or invalid projection")
    if (not _finite_number(before["tick"])
            or not _finite_number(after["tick"])
            or after["tick"] < before["tick"]):
        raise RawAuditError("reset tick is invalid or nonmonotonic")
    if original[TARGET]["block"] != "air":
        raise RawAuditError("pre-task target tile was not empty")
    if original != reset:
        raise RawAuditError("reset guard projection differs from pre-task snapshot")
    if (type(before["copper"]) is not int or type(after["copper"]) is not int
            or before["copper"] != after["copper"]):
        raise RawAuditError("reset copper count differs from pre-task snapshot")
    if (type(before["core_x"]) is not int or type(before["core_y"]) is not int
            or (after["core_x"], after["core_y"]) !=
               (before["core_x"], before["core_y"])):
        raise RawAuditError("reset core location differs from pre-task snapshot")
    if before["source_item"] != "copper" or after["source_item"] != "copper":
        raise RawAuditError("reset copper source is invalid")


def _binding(value: object) -> tuple[int | str, tuple[int, int, int, int]]:
    if type(value) is not dict or set(value) != {"surface", "geometry"}:
        raise RawAuditError("exact before/after geometry binding required")
    surface, geometry = value["surface"], value["geometry"]
    if type(surface) not in (int, str) or surface in (0, ""):
        raise RawAuditError("geometry binding needs nonzero surface identity")
    if (type(geometry) is not list or len(geometry) != 4
            or any(type(item) is not int for item in geometry)
            or geometry[2] <= 0 or geometry[3] <= 0):
        raise RawAuditError("geometry binding needs positive four-integer rectangle")
    return surface, tuple(geometry)


def reconstruct(raw: object) -> dict:
    """Validate lifecycle evidence, then delegate prior event fields to v1."""
    if type(raw) is not dict or set(raw) != RAW_FIELDS:
        raise RawAuditError("exact v2 raw allocation fields required")
    if raw["schema"] != "mindustry_three_arm_raw_events_v2":
        raise RawAuditError("unsupported v2 raw event schema")
    _validate_source_identity(raw["source_identity"])
    arms = raw["arms"]
    if type(arms) is not dict or set(arms) != set(ARMS):
        raise RawAuditError("exact frozen arm set required")

    transitions = raw["transition_events"]
    if type(transitions) is not list or len(transitions) != len(ARMS):
        raise RawAuditError("one raw A3→B1 geometry event per arm required")
    by_arm = {}
    for event in transitions:
        keys = {"arm", "after_task", "before_task", "from_layout", "to_layout",
                "at_ns", "before_binding", "after_binding"}
        if type(event) is not dict or set(event) != keys:
            raise RawAuditError("exact geometry transition event fields required")
        arm = event["arm"]
        if arm not in ARMS or arm in by_arm:
            raise RawAuditError("unknown or duplicate arm geometry event")
        if (event["after_task"], event["before_task"], event["from_layout"],
                event["to_layout"]) != ("A3", "B1", "A", "B"):
            raise RawAuditError("geometry transition must be exactly A3→B1")
        if type(event["at_ns"]) is not int or event["at_ns"] < 0:
            raise RawAuditError("geometry transition timestamp required")
        old_surface, old_geometry = _binding(event["before_binding"])
        new_surface, new_geometry = _binding(event["after_binding"])
        if old_surface != new_surface or old_geometry == new_geometry:
            raise RawAuditError("A3→B1 must keep surface and change geometry")
        by_arm[arm] = event

    base = copy.deepcopy(raw)
    base["schema"] = "mindustry_three_arm_raw_events_v1"
    del base["transition_events"]
    for arm in ARMS:
        tasks = arms[arm]
        if type(tasks) is not list or len(tasks) != len(TASKS):
            raise RawAuditError("six raw task records required per arm")
        reset_events = []
        for index, task in enumerate(tasks):
            if type(task) is not dict or set(task) != TASKS_FIELDS_V2:
                raise RawAuditError("every task needs independent reset evidence")
            reset = task["reset_event"]
            if type(reset) is not dict or set(reset) != {
                    "request_ns", "witness_ns", "receipt_id", "before", "after"}:
                raise RawAuditError("exact private reset event required")
            request, witness = reset["request_ns"], reset["witness_ns"]
            score_ns = task.get("score_event", {}).get("checked_ns")
            if (type(request) is not int or type(witness) is not int
                    or type(score_ns) is not int or not score_ns < request < witness
                    or type(reset["receipt_id"]) is not str or not reset["receipt_id"]):
                raise RawAuditError("independent score must precede reset request and witness")
            _verify_reset(reset["before"], reset["after"])
            reset_events.append(reset)
            if index < len(TASKS) - 1:
                next_start = tasks[index + 1].get("started_ns")
                if type(next_start) is not int or witness >= next_start:
                    raise RawAuditError("next task started before prior reset witness")
            base["arms"][arm][index].pop("reset_event")
        transition = by_arm.get(arm)
        a3_reset = reset_events[2]
        b1_start = raw["arms"][arm][3].get("started_ns")
        if transition is None or type(b1_start) is not int:
            raise RawAuditError("A3→B1 transition or task timing missing")
        if not a3_reset["witness_ns"] < transition["at_ns"] < b1_start:
            raise RawAuditError("geometry change must follow A3 reset and precede B1 ready")

    return reconstruct_v1(base)


def audit(raw_bytes: bytes, expected_source_identity: dict | None = None) -> dict:
    digest = hashlib.sha256(raw_bytes).hexdigest()
    try:
        raw = json.loads(raw_bytes)
        trace = reconstruct(raw)
        if expected_source_identity is not None:
            _validate_source_identity(expected_source_identity)
            if raw["source_identity"] != expected_source_identity:
                raise RawAuditError("raw source identity differs from independent freeze")
        evaluation = _load_evaluator()(trace)
        return {"schema": "mindustry_three_arm_raw_audit_v2",
                "audit": ("PASS_RAW_RECONSTRUCTION" if expected_source_identity is not None
                          else "PASS_CONSTRUCTION_ONLY"),
                "source_identity_verified": expected_source_identity is not None,
                "raw_sha256": digest, "errors": [], "evaluation": evaluation,
                "lifecycle": {"resets_verified": 18, "geometry_transitions_verified": 3},
                "scope": "raw event reconstruction with reset and geometry checks; synthetic until frozen live bytes"}
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
        return {"schema": "mindustry_three_arm_raw_audit_v2",
                "audit": "HOLD_RAW_RECONSTRUCTION", "source_identity_verified": False,
                "raw_sha256": digest, "errors": [str(error)], "evaluation": None,
                "lifecycle": {"resets_verified": 0, "geometry_transitions_verified": 0},
                "scope": "raw event reconstruction with reset and geometry checks; synthetic until frozen live bytes"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("--freeze", type=Path, required=True)
    args = parser.parse_args(argv)
    freeze = json.loads(args.freeze.read_bytes())
    expected = freeze.get("source_identity", freeze) if type(freeze) is dict else freeze
    result = audit(args.raw.read_bytes(), expected_source_identity=expected)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["audit"] == "PASS_RAW_RECONSTRUCTION" else 1


if __name__ == "__main__":
    raise SystemExit(main())
