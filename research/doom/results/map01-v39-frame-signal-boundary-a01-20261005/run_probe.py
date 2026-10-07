"""Run the frozen source-extracted V39 frame-hash boundary probe."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time


ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
SOURCE_COMMIT = "f60752d0fb71595363a80977636ca74c1fd10b21"
SOURCE_PATH = "research/doom/map01_overlap_controller_v39.py"
SOURCE_BLOB = "cdf61eec2c030d7456b34a58907e9c43d5d72084"


def load_source():
    blob = subprocess.run(
        ["git", "rev-parse", f"{SOURCE_COMMIT}:{SOURCE_PATH}"],
        cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    if blob != SOURCE_BLOB:
        raise RuntimeError(f"frozen source blob mismatch: {blob}")
    return subprocess.run(
        ["git", "show", f"{SOURCE_COMMIT}:{SOURCE_PATH}"],
        cwd=ROOT, check=True, capture_output=True).stdout


def extract_monitor(source_bytes):
    parsed = ast.parse(source_bytes)
    wanted = {
        "_typed_json_equal", "_signal_pair_matches",
        "_signal_pair_content_matches", "DoomCoverSignalPairMonitor",
    }
    nodes = [node for node in parsed.body
             if getattr(node, "name", None) in wanted]
    if {node.name for node in nodes} != wanted:
        raise RuntimeError("frozen paired-monitor source is incomplete")
    module = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    namespace = {"time": time}
    exec(compile(module, SOURCE_PATH, "exec"), namespace)
    return namespace["DoomCoverSignalPairMonitor"]


class FixedGuard:
    def __init__(self, signal_id, value):
        self.spec = {"source_value": value, "source_sequence": 10}
        self.source_capture_ns = 1_000_000_000
        self.signal_id = signal_id
        self.value = value

    def evaluate(self, signal):
        if signal.get("signal_id") != self.signal_id or signal.get("value") != self.value:
            return {"status": "UNKNOWN", "reason": "unexpected_signal",
                    "requires_new_decision": True}
        return {"status": "UNCHANGED", "reason": "same_typed_value",
                "requires_new_decision": False,
                "keep_existing_policy": True,
                "grants_input_authority": False,
                "may_only_preserve_or_reduce_existing_authority": True}


def typed_observation(sequence, capture_ns, binding, health, ammo, frame_hash):
    signals = {}
    for signal_id, value in (("health", health), ("ammo", ammo)):
        signals[signal_id] = {
            "format": "observable-signal-v1", "status": "observed",
            "signal_id": signal_id, "value": value,
            "sequence": sequence, "capture_ns": capture_ns,
            "binding": binding,
        }
    return {
        "event": "typed_observation", "sequence": sequence,
        "capture_ns": capture_ns, "pointer_binding": binding,
        "frame_rgb_sha256": frame_hash, "signals": signals,
    }


def main():
    source = load_source()
    monitor_type = extract_monitor(source)
    binding = {"focus": 7, "surface": 9, "geometry": [0, 0, 640, 480]}
    monitor = monitor_type(
        {"health": FixedGuard("health", 84), "ammo": FixedGuard("ammo", 37)},
        health_reader=None, ammo_reader=None)
    first_hash = hashlib.sha256(b"synthetic-frame-baseline").hexdigest()
    second_hash = hashlib.sha256(b"synthetic-frame-changed").hexdigest()
    first = typed_observation(11, 1_100_000_000, binding, 84, 37, first_hash)
    second = typed_observation(12, 1_200_000_000, binding, 84, 37, second_hash)

    first_result = monitor.observe(first)
    second_result = monitor.observe(second)
    outcome = "HOLD"
    if first_result is None:
        outcome = "PASS" if second_result is not None and second_result.get(
            "requires_new_decision") is True else "FAIL"

    raw = {
        "schema": "map01-v39-frame-signal-boundary-raw-v1",
        "experiment_id": "map01-v39-frame-signal-boundary-a01-20261005",
        "source_commit": SOURCE_COMMIT, "source_blob": SOURCE_BLOB,
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "baseline_sequence": first["sequence"],
            "changed_sequence": second["sequence"],
            "baseline_capture_ns": first["capture_ns"],
            "changed_capture_ns": second["capture_ns"],
            "health_values": [84, 84], "ammo_values": [37, 37],
            "frame_hashes": [first_hash, second_hash],
            "binding_unchanged": first["pointer_binding"] == second["pointer_binding"],
        },
        "monitor_outputs": {"baseline": first_result, "changed_frame": second_result},
        "decision": outcome,
        "scope": "source-extracted synthetic construction probe; no live application or input",
    }
    (OUT / "raw.json").write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"decision": outcome, "monitor_outputs": raw["monitor_outputs"],
                      "raw": str(OUT / "raw.json")}, indent=2))


if __name__ == "__main__":
    main()
