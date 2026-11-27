"""One frozen native Win32 fixture trial for delayed effect after expiry.

This script materializes the exact fixture/scorer from the pinned main tree,
freezes the run packet before starting a visible window, and permits one public
dispatch only after checking the exact foreground HWND/PID/title.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PACKET = Path(__file__).resolve().parent
SOURCE_DIR = PACKET / "source"
RAW = PACKET / "raw"
BASE = "490d7bcb4d84927116112e5ff348cdeadfc489d6"
R08 = "research/integration/win32_recorded_task_effect_r08_20261122/source/"


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git_bytes(path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{BASE}:{path}"], cwd=ROOT,
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout


def main() -> int:
    if sys.platform != "win32":
        raise SystemExit("R24 requires the authorized Windows host")
    allowed_top = {Path(__file__).name, "source", "raw"}
    unexpected = ([p.name for p in PACKET.iterdir() if p.name not in allowed_top]
                  if PACKET.exists() else [])
    allowed_preflight = {
        "preflight-normal.log", "preflight-optimized.log",
        "preflight-wrong-cwd-normal.log", "preflight-wrong-cwd-optimized.log",
        "preflight-pythonpath-module-normal.log", "preflight-pythonpath-module-optimized.log",
        "preflight-main-normal.log", "preflight-main-optimized.log",
    }
    existing_raw = list(RAW.iterdir()) if RAW.exists() else []
    source_names = {"fixture_app.py", "scorer.py", "foreground_probe.py", "live_probe.py"}
    existing_source = list(SOURCE_DIR.iterdir()) if SOURCE_DIR.exists() else []
    raw_dirs = [p for p in existing_raw if p.is_dir()]
    raw_files = [p for p in existing_raw if p.is_file()]
    nested_raw_data = any(p.is_file() for folder in raw_dirs for p in folder.rglob("*"))
    if (unexpected or any(p.name not in allowed_preflight for p in raw_files)
            or any(p.name not in {"mcp", "recorder"} for p in raw_dirs)
            or nested_raw_data
            or any(p.name not in source_names for p in existing_source)):
        raise SystemExit("R24 packet path already contains data; refusing overwrite")
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "mcp").mkdir(exist_ok=True)
    recorder = RAW / "recorder"
    (recorder / "raw").mkdir(parents=True, exist_ok=True)

    files = {
        "fixture_app.py": R08 + "fixture_app.py",
        "scorer.py": R08 + "scorer.py",
        "foreground_probe.py": R08 + "foreground_probe.py",
        "live_probe.py": R08 + "live_probe.py",
    }
    for name, repo_path in files.items():
        data = git_bytes(repo_path)
        if name == "fixture_app.py":
            data = data.replace(b"Agent Interface Win32 Fixture", b"Agent Interface Win32 Fixture R24")
        elif name == "foreground_probe.py":
            data = data.replace(b'== "Agent Interface Win32 Fixture"', b'== "Agent Interface Win32 Fixture R24"')
        elif name == "live_probe.py":
            source = data.decode("utf-8")
            if source.count("now+60_000_000_000") != 1:
                raise RuntimeError("pinned R08 authority lease expression changed")
            source = source.replace("now+60_000_000_000", "now+cfg['authority_lease_ms']*1_000_000")
            region_expr = "x1,y1,x2,y2=window['rect']; region=[x1,y1,x2-x1,y2-y1]"
            frame_expr = "'frame':'screen_physical_px'"
            if source.count(region_expr) != 1 or source.count(frame_expr) != 2:
                raise RuntimeError("pinned R08 runner capture contract changed")
            source = source.replace("'frame':'screen_physical_px'", "'frame':cfg['capture_frame']")
            source = source.replace("x1,y1,x2,y2=window['rect']; region=[x1,y1,x2-x1,y2-y1]",
                                    "region=cfg['capture_region']")
            old = ("'native_owner_evidence':{'lookup_tool_call_id':exact_id,"
                   "'action_call_id':action_id,'effect_observed_ns':"
                   "effect.get('effect_observed_ns') if effect else None}")
            new = ("'effect_attribution':{'effect_observed_ns':"
                   "effect.get('effect_observed_ns') if effect else None,"
                   "'authority_expiry_ns':program['authority']['expires_at_ns'],"
                   "'release_received_ns':owner.get('action',{}).get('completion_custody',{}).get('completion_release_receipt',{}).get('monotonic_ns'),"
                   "'horizon_end_ns':owner.get('action',{}).get('completion_custody',{}).get('completion_readback',{}).get('late_input_observation_end_monotonic_ns',owner.get('action',{}).get('completion_custody',{}).get('completion_readback',{}).get('late_input_observation_end_ns'))}")
            if source.count(old) != 1:
                raise RuntimeError("pinned R08 runner no longer matches the audited adaptation seam")
            data = source.replace(old, new).encode("utf-8")
        (SOURCE_DIR / name).write_bytes(data)

    ids = {name: uuid.uuid4().hex for name in (
        "observe_before", "dispatch_boundary", "results_exact",
        "observe_after", "close_boundary")}
    run_id = uuid.uuid4().hex
    checkout_commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                     check=True, capture_output=True, text=True).stdout.strip()
    checkout_runtime_tree = subprocess.run(["git", "rev-parse", "HEAD:runtime"], cwd=ROOT,
                                           check=True, capture_output=True, text=True).stdout.strip()
    main_runtime_tree = subprocess.run(["git", "rev-parse", f"{BASE}:runtime"], cwd=ROOT,
                                       check=True, capture_output=True, text=True).stdout.strip()
    checkout_ledger_tree = subprocess.run(["git", "rev-parse", "HEAD:research/integration/standard_mcp_task_ledger_57_v1"],
                                          cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    main_ledger_tree = subprocess.run(["git", "rev-parse", f"{BASE}:research/integration/standard_mcp_task_ledger_57_v1"],
                                      cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    if checkout_runtime_tree != main_runtime_tree or checkout_ledger_tree != main_ledger_tree:
        raise RuntimeError("execution checkout differs from current-main runtime/ledger trees")
    env = {
        "python": sys.version,
        "platform": platform.platform(),
        "main_commit": BASE,
        "loaded_checkout_commit": checkout_commit,
        "runtime_tree_git_id": checkout_runtime_tree,
        "standard_ledger_tree_git_id": checkout_ledger_tree,
        "provider": "none",
        "model": "none",
        "display": os.environ.get("SESSIONNAME", "interactive Windows session"),
    }
    (RAW / "environment.json").write_text(json.dumps(env, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    source_hashes = {name: hashlib.sha256((SOURCE_DIR / name).read_bytes()).hexdigest()
                     for name in files}
    conditions = {
        "experiment": "win32-expired-authority-delayed-effect-r24",
        "status": "FROZEN",
        "run_id": run_id,
        "source_main": BASE,
        "loaded_checkout_commit": checkout_commit,
        "source_tree_identity": {"runtime": checkout_runtime_tree,
                                 "standard_mcp_task_ledger": checkout_ledger_tree},
        "scope": "one new visible Win32 fixture; public observe/dispatch/results/observe/close; one focus+A+release_all action; fixture schedules delayed text after authority expiry; independent event/effect scorer; no provider/model; no retry",
        "provider": "none",
        "model": "none",
        "target_title": "Agent Interface Win32 Fixture R24",
        "capture_frame": "window_client",
        "capture_region": [0, 0, 400, 180],
        "fixture_delay_ms": 6000,
        "authority_lease_ms": 2000,
        "horizon_ms": 2000,
        "max_horizon_gap_ms": 100,
        "program_id": "r24-" + uuid.uuid4().hex,
        "lease_id": "r24-" + uuid.uuid4().hex,
        "recorder_call_ids": ids,
        "task_id": "r24-delayed-a-after-expiry-" + run_id,
        "scorer_id": "fixture-delayed-a-independent-v1",
        "source_hashes_sha256": source_hashes,
        "environment_sha256": hashlib.sha256((RAW / "environment.json").read_bytes()).hexdigest(),
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "orchestration_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "stop_rules": [
            "Create exactly one fresh fixture and verify exact HWND/PID/title as foreground before the first public observation.",
            "Observe with no-authority/no-input and verify the exact PNG/raw hashes before dispatch.",
            "Dispatch one action only; no replay. Lease is 2 s; fixture effect timer is frozen at 6 s.",
            "Preserve exact results, release and full 2 s neutral horizon; do not close the target if either is unknown.",
            "Score final text and key-down/key-up independently from fixture event/effect files.",
            "Expected adjudication: factual effect may be true; an interval crossing authority expiry is ambiguous/ineligible, never promoted to authorized task success.",
            "If foreground, observation, dispatch, cleanup or receipt is ambiguous, preserve raw and stop without retry.",
        ],
        "not_claimed": ["recovery reliability", "matched efficiency", "MAP01", "Research Preview graduation", "general GUI reliability"],
    }
    write_json(PACKET / "conditions.json", conditions)
    print(json.dumps({"frozen": True, "run_id": run_id, "source_main": BASE,
                      "conditions_sha256": hashlib.sha256((PACKET / "conditions.json").read_bytes()).hexdigest(),
                      "source_hashes": source_hashes}, indent=2))

    meta = RAW / "fixture-meta.json"
    effect = RAW / "effect.json"
    events = RAW / "events.jsonl"
    stdout = (RAW / "fixture.stdout.txt").open("wb")
    stderr = (RAW / "fixture.stderr.txt").open("wb")
    process = subprocess.Popen([
        sys.executable, str(SOURCE_DIR / "fixture_app.py"),
        "--meta", str(meta), "--effect", str(effect), "--events", str(events),
        "--effect-delay-ms", "6000",
    ], cwd=PACKET, stdout=stdout, stderr=stderr)
    write_json(RAW / "fixture-process-start.json", {"pid": process.pid, "started_ns": time.monotonic_ns()})

    deadline = time.monotonic() + 10
    while time.monotonic() < deadline and not meta.exists() and process.poll() is None:
        time.sleep(0.05)
    if not meta.exists():
        write_json(RAW / "fixture-start-stop.json", {"status": "STOP_FIXTURE_NOT_READY", "exit_code": process.poll()})
        stdout.close(); stderr.close()
        return 2
    fixture_meta = json.loads(meta.read_text(encoding="utf-8"))
    hwnd = int(fixture_meta["hwnd"])
    pid = process.pid

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    class RECT(ctypes.Structure):
        _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long), ("bottom", ctypes.c_long)]
    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
    user32.GetClientRect.argtypes = [ctypes.c_void_p, ctypes.POINTER(RECT)]
    user32.GetClientRect.restype = ctypes.c_int
    rect = RECT()
    if not user32.GetClientRect(hwnd, ctypes.byref(rect)):
        raise OSError(ctypes.get_last_error(), "GetClientRect failed")
    write_json(RAW / "targets.json", {"fixture": hwnd})
    write_json(RAW / "window.json", {"hwnd": hwnd, "pid": pid, "title": conditions["target_title"],
                                      "rect": [0, 0, rect.right - rect.left, rect.bottom - rect.top],
                                      "frame": conditions["capture_frame"],
                                      "configured_region": conditions["capture_region"]})

    probe = subprocess.run([sys.executable, str(SOURCE_DIR / "foreground_probe.py"),
                            str(hwnd), str(pid), str(RAW / "foreground-pre-dispatch.json")],
                           cwd=PACKET, capture_output=True, text=True)
    (RAW / "foreground-pre-dispatch.stdout.txt").write_text(probe.stdout, encoding="utf-8")
    (RAW / "foreground-pre-dispatch.stderr.txt").write_text(probe.stderr, encoding="utf-8")
    if probe.returncode:
        write_json(RAW / "runner-exit.json", {"status": "STOP_FOREGROUND_MISMATCH", "exit_code": probe.returncode})
        user32.PostMessageW(ctypes.c_void_p(hwnd), 0x0010, 0, 0)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        stdout.close(); stderr.close()
        return 3

    try:
        runner = subprocess.run([sys.executable, str(SOURCE_DIR / "live_probe.py"), str(ROOT), str(PACKET)],
                                cwd=ROOT, capture_output=True, text=True, timeout=120)
        (RAW / "runner.stdout.txt").write_text(runner.stdout, encoding="utf-8")
        (RAW / "runner.stderr.txt").write_text(runner.stderr, encoding="utf-8")
        write_json(RAW / "runner-exit.json", {"exit_code": runner.returncode, "finished_ns": time.monotonic_ns()})
    except subprocess.TimeoutExpired as exc:
        write_json(RAW / "runner-timeout.json", {"status": "STOP_RUNNER_TIMEOUT_UNKNOWN", "timeout_seconds": 120,
                                                  "stdout": str(exc.stdout or ""), "stderr": str(exc.stderr or "")})
        stdout.close(); stderr.close()
        return 4

    summary_path = RAW / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else None
    safe_to_close = bool(summary and summary.get("release_confirmed") is True
                         and summary.get("late_input_horizon_verified") is True)
    if safe_to_close:
        WM_CLOSE = 0x0010
        user32.PostMessageW(ctypes.c_void_p(hwnd), WM_CLOSE, 0, 0)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            safe_to_close = False
    write_json(RAW / "fixture-cleanup.json", {"close_requested": safe_to_close,
                                               "pid": pid, "hwnd": hwnd,
                                               "exit_code": process.poll(),
                                               "release_and_horizon_precondition": bool(summary and summary.get("release_confirmed") is True and summary.get("late_input_horizon_verified") is True)})
    stdout.close(); stderr.close()
    return runner.returncode


if __name__ == "__main__":
    raise SystemExit(main())
