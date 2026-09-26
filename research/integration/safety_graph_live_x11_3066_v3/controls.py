"""Synthetic corruption controls for audit.py; never consumes experiment RAW."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ALLOCATION = "safety-graph-live-x11-3066-20260926-v3-01"
CONFIGS = ("bare", "openbox")
SCHEDULES = ("normal", "ipc_delay", "display_stall", "owner_death", "target_replacement", "cleanup_failure", "unknown_dependency")


def fixture() -> list[dict]:
    rows = []
    for config in CONFIGS:
        for schedule in SCHEDULES:
            unknown = schedule == "unknown_dependency"
            cleanup_failure = schedule == "cleanup_failure"
            owner_death = schedule == "owner_death"
            processes = [
                {"role": "runner", "pid": 1, "present": True, "ppid": 0, "fd_links": {"7": "pipe:[123]"}, "unix_socket_paths": []},
                {"role": "xvfb", "pid": 2, "present": True, "ppid": 1, "fd_links": {}, "unix_socket_paths": []},
                {"role": "openbox", "pid": 3 if config == "openbox" else None, "present": config == "openbox", "ppid": 1 if config == "openbox" else None, "fd_links": {}, "unix_socket_paths": []},
                {"role": "observer", "pid": 4, "present": True, "ppid": 1, "fd_links": {}, "unix_socket_paths": []},
                {"role": "worker", "pid": None if unknown else 5, "present": not unknown, "ppid": 1 if not unknown else None, "fd_links": {"1": "pipe:[123]"}, "unix_socket_paths": []},
            ]
            start = {"authority_deadline_ns": 10_000_000_000, "loaded_runtime": {
                "session": "runtime.backends.x11_v1.session.X11RuntimeSession",
                "backend": "__main__.FailingReleaseBackend" if cleanup_failure else "runtime.backends.x11_v1.backend.X11Backend",
                "dispatch_facade": "runtime.cli_v1.api.dispatch",
            }}
            dispatch = {"status": "execution_failed", "recovery_required": True,
                        "execution": {"error": "RuntimeError('INJECTED_RELEASE_PATH_FAILURE')"}}
            receipt = None if owner_death or unknown else {"dispatch_result": {"result": dispatch if cleanup_failure else {"status": "completed"}}}
            row = {
                "allocation": ALLOCATION, "config": config, "schedule": schedule,
                "display": ":610", "processes": processes, "unix_sockets_by_inode": {},
                "terminal_key_down": False, "worker_start_receipt": None if unknown else start,
                "worker_receipt": receipt, "worker_returncode": -9 if owner_death else 0,
                "release_witness_upper_bound_ns": None if unknown or cleanup_failure or owner_death else 10_000_000_100,
                "supervisor_release": {"finished_ns": 10_000_000_100} if cleanup_failure or owner_death else None,
                "execution_disposition": "STOP_UNKNOWN_DEPENDENCY" if unknown else None,
                "typed_stop": unknown, "input_dispatched": False if unknown else None,
                "worker_pid": None if unknown else 5,
                "worker_stdout_fd": 7, "worker_stdout_link": None if unknown else "pipe:[123]",
                "parent_stdout_link": None if unknown else "pipe:[123]",
            }
            rows.append(row)
    return rows


def run_audit(rows: list[dict], root: Path, name: str) -> str:
    raw_path = root / f"{name}.raw.json"
    report_path = root / f"{name}.audit.json"
    raw_path.write_text(json.dumps(rows), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(HERE / "audit.py"), str(raw_path), "--out", str(report_path)],
        capture_output=True, text=True, check=False,
    )
    if not report_path.exists():
        raise RuntimeError(f"{name}: auditor produced no report: {result.stderr}")
    return json.loads(report_path.read_text(encoding="utf-8"))["decision"]


def main() -> int:
    controls = []
    with tempfile.TemporaryDirectory(prefix="ai3066-v3-controls-") as directory:
        root = Path(directory)
        baseline = fixture()
        baseline_decision = run_audit(baseline, root, "baseline")
        if baseline_decision != "PASS_SAFETY_GRAPH_RUNTIME_RECONCILIATION_SCOPED":
            raise RuntimeError(f"synthetic baseline did not pass: {baseline_decision}")
        controls.append({"name": "synthetic_complete_baseline", "decision": baseline_decision, "expected": "PASS"})

        cases = []
        dropped = copy.deepcopy(baseline); dropped.pop(); cases.append(("drop_case", dropped, "HOLD"))
        duplicate = copy.deepcopy(baseline); duplicate[-1] = copy.deepcopy(duplicate[0]); cases.append(("duplicate_identity", duplicate, "HOLD"))
        hidden = copy.deepcopy(baseline); hidden[0]["processes"][3]["unix_socket_paths"] = ["/tmp/undeclared.sock"]; cases.append(("hidden_named_socket", hidden, "FAIL"))
        late = copy.deepcopy(baseline); late[0]["release_witness_upper_bound_ns"] = 10_050_000_001; cases.append(("late_release", late, "FAIL"))
        down = copy.deepcopy(baseline); down[0]["terminal_key_down"] = True; cases.append(("terminal_key_down", down, "FAIL"))
        unknown_dispatch = copy.deepcopy(baseline); unknown_dispatch[-1]["worker_pid"] = 77; cases.append(("unknown_dependency_spawned_worker", unknown_dispatch, "HOLD"))
        unknown_socket = copy.deepcopy(baseline); unknown_socket[0]["processes"][3]["fd_links"] = {"7": "socket:[12345]"}; cases.append(("unclassified_socket_fd", unknown_socket, "HOLD"))
        wrong_runtime = copy.deepcopy(baseline); wrong_runtime[0]["worker_start_receipt"]["loaded_runtime"]["dispatch_facade"] = "test.fake.dispatch"; cases.append(("wrong_facade", wrong_runtime, "HOLD"))
        for name, rows, expected in cases:
            decision = run_audit(rows, root, name)
            matched = decision.startswith(expected)
            controls.append({"name": name, "decision": decision, "expected": expected, "passed": matched})
            if not matched:
                raise RuntimeError(f"{name}: expected {expected}, got {decision}")
    print(json.dumps({"formal_invocations": 0, "control_count": len(controls) - 1,
                      "synthetic_baseline": controls[0], "controls": controls[1:]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
