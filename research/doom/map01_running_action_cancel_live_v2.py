"""One frozen live OS-input probe for mid-hold running-action cancellation."""
import argparse
import atexit
import hashlib
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LIVE = HERE.parent / "live_control"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(LIVE))
from action_validity_admission_v1 import evaluate_action_validity
from doom_action_snapshot_v1 import build_action_snapshot
from doom_action_validity_contract_v1 import build_contract
from doom_hud_signal_v2 import DoomStatusNumberReader
from map01_overlap_controller_v34 import (
    DoomRunningActionMonitor, cancel_invalidated_action, compile_commands)
from running_action_guard_v1 import RunningActionGuard


PREREG = HERE / "map01_running_action_cancel_live_v2_prereg.json"
WAD = REPO / "_vizdoom/vizdoom/freedoom2.wad"


def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(plan):
    checks = {name: (REPO / name).is_file() and sha(REPO / name) == digest
              for name, digest in plan["source_sha256"].items()}
    checks["output_absent"] = not (REPO / plan["output"]).exists()
    checks["one_episode_no_retry"] = plan["episodes"] == 1 and plan["retry_limit"] == 0
    checks["no_model"] = plan["model_calls"] == 0
    checks["latency_thresholds"] = (
        plan["thresholds_ms"]["capture_to_cancel_requested_lte"] == 150 and
        plan["thresholds_ms"]["capture_to_release_verified_lte"] == 200)
    return checks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    plan = read(PREREG)
    verification = verify(plan)
    if args.verify_only:
        print(json.dumps({"passed": all(verification.values()), "checks": verification}, indent=2))
        return 0 if all(verification.values()) else 1
    if not all(verification.values()):
        raise RuntimeError(f"frozen live probe verification failed: {verification}")
    if os.name == "nt" or not Path("/mnt/c").is_dir():
        raise RuntimeError("run this X11/VizDoom allocation from WSL")

    output = REPO / plan["output"]
    output.mkdir(parents=True, exist_ok=False)
    runtime = output / "runtime"
    fixture = REPO / plan["fixture_manifest"]
    # WAD parsing/template construction must precede the freshness source.
    health_reader = DoomStatusNumberReader(WAD, signal_id="health")
    ammo_reader = DoomStatusNumberReader(WAD, signal_id="ammo")
    command = [sys.executable, str(HERE / "session_map01_v7.py"),
               "--out", str(runtime), "--seed", str(plan["seed"]),
               "--timeout-seconds", "30", "--skill", "1",
               "--load-fixture-manifest", str(fixture)]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, bufsize=1)
    def cleanup_process():
        if process.poll() is not None: return
        try:
            process.stdin.write('{"op":"finish"}\n'); process.stdin.flush()
        except (BrokenPipeError, OSError, ValueError):
            pass
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.terminate()
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait(timeout=5)
    atexit.register(cleanup_process)
    incoming = queue.Queue(); events = []; latest = None
    def reader():
        for line in process.stdout:
            row = json.loads(line); events.append(row); incoming.put(row)
    threading.Thread(target=reader, daemon=True).start()
    def wait(predicate, timeout=20, observation_monitor=None):
        nonlocal latest
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try: row = incoming.get(timeout=min(.25, max(.01, deadline-time.monotonic())))
            except queue.Empty:
                if process.poll() is not None:
                    raise RuntimeError("session exited: " + process.stderr.read())
                continue
            if row.get("event") == "observation":
                latest = row
                if observation_monitor is not None:
                    invalidation = observation_monitor.observe(row)
                    if invalidation is not None: return invalidation
            if predicate(row): return row
        raise TimeoutError("expected runtime event")

    ready = wait(lambda row: row.get("event") == "ready")
    initial_observation = wait(lambda row: row.get("event") == "observation")
    source_health = health_reader.read(initial_observation)
    source_ammo = ammo_reader.read(initial_observation)
    if (source_health["status"] != "observed" or
            source_ammo["status"] != "observed"):
        raise RuntimeError("initial visible HUD signals unavailable")
    action = [{"action": "fire", "extent": "long"}]
    authored = {"critical_health_minimum": 1, "maximum_health_loss": 20,
                "minimum_ammo": source_ammo["value"], "max_current_age_ms": 500}
    contract = build_contract(action, authored, source_health, source_ammo)
    readers = {"health": health_reader, "ammo": ammo_reader}
    initial_snapshot = build_action_snapshot(initial_observation, contract, readers)
    initial_validity = evaluate_action_validity(
        action, contract, initial_snapshot, time.perf_counter_ns())
    if initial_validity["status"] != "VALID_CURRENT":
        raise RuntimeError(initial_validity)
    guard = RunningActionGuard(action, contract, initial_validity)
    monitor = DoomRunningActionMonitor(guard, health_reader, ammo_reader)

    identifier = "running-action-fire-02"
    sent_ns = time.perf_counter_ns()
    process.stdin.write(json.dumps({"op": "submit", "id": identifier,
        "expected_sequence": latest["sequence"],
        "valid_until_ns": sent_ns + 5_000_000_000,
        "steps": compile_commands(action)}) + "\n")
    process.stdin.flush()
    accepted = wait(lambda row: row.get("event") in ("accepted", "rejected"))
    if accepted["event"] != "accepted": raise RuntimeError(accepted)
    guard.admit_program({"event": "accepted", "id": identifier,
                         "accepted_ns": accepted["accepted_ns"]})
    boundary = wait(lambda row: row.get("event") == "terminal" and
                    row.get("id") == identifier, observation_monitor=monitor)
    if boundary.get("event") != "running_action_invalidation":
        raise RuntimeError("held input completed before a visible running invalidation")
    cancel_event, terminal, guard_receipt = cancel_invalidated_action(
        process, wait, identifier, guard)
    invalidity = guard_receipt["invalidation"]["result"]
    capture_ns = invalidity["snapshot"]["capture_ns"]
    decided_ns = invalidity["controller_decided_ns"]
    first_program_observation = next(row for row in events
        if row.get("event") == "observation" and row.get("id") == identifier)
    process.stdin.write('{"op":"finish"}\n'); process.stdin.flush()
    score = wait(lambda row: row.get("event") == "post_control_score")
    process.wait(timeout=20)
    atexit.unregister(cleanup_process)
    stderr = process.stderr.read(); (output / "stderr.txt").write_text(stderr)
    metrics = {
        "submit_send_to_accept_ms": (accepted["accepted_ns"] - sent_ns) / 1e6,
        "accept_to_first_observation_capture_ms":
            (first_program_observation["capture_ns"] - accepted["accepted_ns"]) / 1e6,
        "accept_to_first_observation_emit_ms":
            (first_program_observation["emit_ns"] - accepted["accepted_ns"]) / 1e6,
        "accept_to_invalidation_capture_ms": (capture_ns - accepted["accepted_ns"]) / 1e6,
        "capture_to_guard_decision_ms": (decided_ns - capture_ns) / 1e6,
        "capture_to_cancel_requested_ms": (cancel_event["requested_ns"] - capture_ns) / 1e6,
        "guard_decision_to_cancel_requested_ms":
            (cancel_event["requested_ns"] - decided_ns) / 1e6,
        "capture_to_release_verified_ms":
            (terminal["release"]["verified_ns"] - capture_ns) / 1e6,
        "guard_decision_to_release_verified_ms":
            (terminal["release"]["verified_ns"] - decided_ns) / 1e6,
    }
    checks = {
        "ammo_decreased_on_screen":
            invalidity["snapshot"]["signals"]["ammo"]["value"] < source_ammo["value"],
        "ammo_predicate_triggered": invalidity["reason"] == "ammo_minimum_failed",
        "matched_cancel": cancel_event["matched"] is True,
        "cancelled_terminal": terminal["status"] == "cancelled",
        "empty_release": guard_receipt["physical_release_verified"] is True,
        "capture_to_cancel_within_threshold": metrics["capture_to_cancel_requested_ms"] <= 150,
        "capture_to_release_within_threshold": metrics["capture_to_release_verified_ms"] <= 200,
        "process_exit_zero": process.returncode == 0,
    }
    report = {"allocation_id": plan["allocation_id"], "passed": all(checks.values()),
              "verification": verification, "checks": checks,
              "ready": ready, "action": action, "authored_validity": authored,
              "source_signals": {"health": source_health, "ammo": source_ammo},
              "initial_validity": initial_validity,
              "running_guard": guard_receipt, "cancel_event": cancel_event,
              "terminal": terminal, "metrics_ms": metrics, "score": score,
              "runtime_process_exit": process.returncode,
              "model_calls": 0, "scope": plan["scope"]}
    (output / "report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"passed": report["passed"], "checks": checks,
                      "metrics_ms": metrics}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

