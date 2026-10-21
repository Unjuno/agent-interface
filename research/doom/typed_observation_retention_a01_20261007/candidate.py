#!/usr/bin/env python3
"""Replay current-main session event persistence with representative typed rows."""
import ast
import contextlib
import hashlib
import io
import json
import subprocess
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_path(relative):
    return ROOT / relative


def load_emit(source, out):
    tree = ast.parse(source, filename="session_map01_v12.py")
    main = next(node for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == "main")
    emit_node = next(node for node in main.body
                     if isinstance(node, ast.FunctionDef) and node.name == "emit")
    factory = ast.FunctionDef(
        name="_factory",
        args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[],
                           kw_defaults=[], defaults=[]),
        body=[
            ast.Assign(targets=[ast.Name(id="latest_observation", ctx=ast.Store())],
                       value=ast.Constant(None)),
            ast.Assign(
                targets=[ast.Name(id="lock", ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Attribute(value=ast.Name(id="threading", ctx=ast.Load()),
                                       attr="RLock", ctx=ast.Load()),
                    args=[], keywords=[])),
            emit_node,
            ast.Return(value=ast.Name(id="emit", ctx=ast.Load())),
        ], decorator_list=[])
    module = ast.fix_missing_locations(ast.Module(body=[factory], type_ignores=[]))
    namespace = {"json": json, "threading": threading, "time": time,
                 "args": SimpleNamespace(out=out)}
    exec(compile(module, "session_map01_v12.py:emit", "exec"), namespace)
    return namespace["_factory"]()


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 candidate.py OUT_DIR")
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=False)

    source_hashes = {}
    for relative, expected in FREEZE["source_files"].items():
        actual = sha256(source_path(relative))
        if actual != expected:
            raise SystemExit(f"source hash mismatch: {relative}: {actual}")
        source_hashes[relative] = actual

    session_source = source_path("research/doom/session_map01_v12.py").read_text()
    backend_source = source_path("research/doom/doom_typed_coast_backend_v1.py").read_text()
    backend_lines = backend_source.splitlines()
    order = {
        "typed_emit": next(i for i, line in enumerate(backend_lines, 1)
                           if "self.emit(typed)" in line),
        "artifact_publish": next(i for i, line in enumerate(backend_lines, 1)
                                  if "self.images.publish(frame)" in line),
        "full_observation": next(i for i, line in enumerate(backend_lines, 1)
                                  if '"event": "observation"' in line),
    }
    if not order["typed_emit"] < order["artifact_publish"] < order["full_observation"]:
        raise SystemExit(f"backend event ordering failed: {order}")

    binding = {"focus": 1, "surface": 1, "geometry": [0, 0, 640, 480]}
    typed = {
        "event": "typed_observation", "schema": "doom-typed-observation-v1",
        "id": "synthetic-plan-1", "step": 0, "sequence": 7,
        "capture_ns": 100, "pointer_binding": binding,
        "signals": {
            name: {"format": "observable-signal-v1", "status": "observed",
                   "signal_id": name, "value": value, "sequence": 7,
                   "capture_ns": 100, "binding": binding,
                   "wad_sha256": "b" * 64}
            for name, value in (("health", 81), ("ammo", 23))
        },
        "frame_rgb_sha256": "a" * 64, "frame_size": [640, 480],
        "typed_extraction_started_ns": 101, "typed_ready_ns": 102,
        "capture_to_typed_ready_ms": 0.000002,
        "artifact_published": False, "grants_input_authority": False,
    }
    full = {
        "event": "observation", "id": "synthetic-plan-1", "step": 0,
        "sequence": 7, "capture_ns": 100, "exact": True,
        "pointer_binding": binding, "image": "synthetic-frame.png",
        "frame_rgb_sha256": "a" * 64, "semantic_completion": "unknown",
    }
    emit = load_emit(session_source, out)
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        emit(dict(typed))
        emit(dict(full))

    event_path = out / "events.jsonl"
    delivered_path = out / "delivered.jsonl"
    event_rows = [json.loads(line) for line in event_path.read_text().splitlines()]
    delivered_rows = [json.loads(line) for line in delivered_path.read_text().splitlines()]
    expected_events = ["typed_observation", "observation"]
    if [row.get("event") for row in event_rows] != expected_events:
        raise SystemExit("event order or membership mismatch")
    if event_rows != delivered_rows:
        raise SystemExit("delivered stream differs from raw event stream")
    if (event_rows[0].get("signals", {}).get("health", {}).get("value") != 81 or
            event_rows[0].get("signals", {}).get("ammo", {}).get("value") != 23):
        raise SystemExit("nested health/ammo values did not survive persistence")
    if any(type(row.get("emit_ns")) is not int for row in event_rows):
        raise SystemExit("event emission timestamp missing or not integer")

    result = {
        "schema": "typed-observation-retention-result-v1",
        "allocation_id": FREEZE["allocation_id"],
        "result": "PASS_TYPED_SIGNAL_RAW_RETENTION_BOUNDARY",
        "source_commit": FREEZE["source_commit"],
        "execution_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_hashes": source_hashes,
        "events": len(event_rows),
        "event_order": expected_events,
        "typed_health": 81,
        "typed_ammo": 23,
        "delivered_matches_events": True,
        "emit_timestamps_present": True,
        "backend_source_lines": order,
        "event_stream_sha256": sha256(event_path),
        "delivered_stream_sha256": sha256(delivered_path),
        "controller_monitor_outcomes_in_this_replay": 0,
        "game_model_gui_input": 0,
    }
    (out / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
