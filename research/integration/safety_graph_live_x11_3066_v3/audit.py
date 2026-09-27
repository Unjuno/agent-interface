"""Independent raw-evidence gate for the Issue #3066 v3 allocation.

This file deliberately does not import the runtime or run.py.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ALLOCATION = "safety-graph-live-x11-3066-20260926-v3-01"
CONFIGS = ("bare", "openbox")
SCHEDULES = ("normal", "ipc_delay", "display_stall", "owner_death", "target_replacement", "cleanup_failure", "unknown_dependency")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raw = json.loads(args.raw.read_text(encoding="utf-8"))
    issues: list[str] = []
    graph_findings: list[dict] = []
    expected = {(config, schedule) for config in CONFIGS for schedule in SCHEDULES}
    found = {(r.get("config"), r.get("schedule")) for r in raw if isinstance(r, dict)}
    if len(raw) != 14 or found != expected or len(found) != len(raw):
        issues.append("DENOMINATOR_OR_IDENTITY_MISMATCH")
    if any(not isinstance(r, dict) or r.get("allocation") != ALLOCATION for r in raw):
        issues.append("ALLOCATION_MISMATCH")

    hidden = []
    release_violations = []
    for row in raw:
        identity = f"{row.get('config')}/{row.get('schedule')}"
        processes = row.get("processes")
        if not isinstance(processes, list) or len(processes) != 5:
            issues.append(f"{identity}:PROCESS_GRAPH_MISSING")
            continue
        by_role = {p.get("role"): p for p in processes if isinstance(p, dict)}
        if set(by_role) != {"runner", "xvfb", "openbox", "observer", "worker"}:
            issues.append(f"{identity}:PROCESS_ROLES_INVALID")
            continue
        runner_pid = by_role["runner"].get("pid")
        for role, proc in by_role.items():
            if role != "runner" and proc.get("present") and proc.get("ppid") != runner_pid:
                issues.append(f"{identity}:{role}:PARENT_EDGE_MISMATCH")
        allowed = {"runner", "xvfb", "openbox", "observer", "worker"}
        sockets = row.get("unix_sockets_by_inode", {})
        if not isinstance(sockets, dict):
            issues.append(f"{identity}:SOCKET_INODE_TABLE_MISSING")
            sockets = {}
        declared_sockets = {f"/tmp/.X11-unix/X{int(row['display'][1:])}"}
        for role, proc in by_role.items():
            if not proc.get("present"):
                continue
            for link in proc.get("fd_links", {}).values():
                if not link.startswith("socket:["):
                    continue
                inode = link[8:-1]
                if inode not in sockets or not sockets.get(inode):
                    issues.append(f"{identity}:{role}:UNCLASSIFIED_SOCKET_FD:{inode}")
            for path in proc.get("unix_socket_paths", []):
                if path not in declared_sockets:
                    hidden.append({"case": identity, "role": role, "socket": path})
        # The intended X server, window manager, independent target observer,
        # and one runtime worker are the complete declared graph.
        graph_findings.append({
            "case": identity,
            "declared_roles": sorted(allowed),
            "present_roles": sorted(role for role, p in by_role.items() if p.get("present")),
            "declared_socket_paths": sorted(declared_sockets),
            "sampled_socket_inodes": len(sockets),
            "fd_snapshot_races": {role: p.get("fd_snapshot_races", []) for role, p in by_role.items() if p.get("fd_snapshot_races")},
        })
        if row.get("schedule") == "unknown_dependency":
            if row.get("execution_disposition") != "STOP_UNKNOWN_DEPENDENCY" or row.get("input_dispatched") is not False:
                issues.append(f"{identity}:UNKNOWN_NOT_TYPED_STOP")
            if row.get("worker_pid") is not None:
                issues.append(f"{identity}:UNKNOWN_SPAWNED_WORKER")
            if row.get("terminal_key_down") is not False:
                issues.append(f"{identity}:UNKNOWN_LEFT_INPUT_DOWN")
        else:
            worker_pipe = row.get("worker_stdout_link")
            parent_pipe = row.get("parent_stdout_link")
            runner_fds = by_role["runner"].get("fd_links", {})
            if (not isinstance(worker_pipe, str) or not worker_pipe.startswith("pipe:[") or
                    worker_pipe != parent_pipe or
                    runner_fds.get(str(row.get("worker_stdout_fd"))) != parent_pipe):
                issues.append(f"{identity}:WORKER_RESULT_PIPE_UNRECONCILED")
            receipt = row.get("worker_receipt")
            start_receipt = row.get("worker_start_receipt")
            if not isinstance(start_receipt, dict):
                issues.append(f"{identity}:WORKER_START_RECEIPT_MISSING")
                continue
            if not isinstance(receipt, dict) and row.get("schedule") != "owner_death":
                issues.append(f"{identity}:WORKER_RECEIPT_MISSING")
                continue
            expected_backend = "FailingReleaseBackend" if row.get("schedule") == "cleanup_failure" else "X11Backend"
            for field, suffix in (("session", "X11RuntimeSession"), ("backend", expected_backend)):
                if not str(start_receipt.get("loaded_runtime", {}).get(field, "")).endswith(suffix):
                    issues.append(f"{identity}:WRONG_RUNTIME_CLASS:{field}")
            if start_receipt.get("loaded_runtime", {}).get("dispatch_facade") != "runtime.cli_v1.api.dispatch":
                issues.append(f"{identity}:PUBLIC_FACADE_NOT_USED")
            deadline = start_receipt.get("authority_deadline_ns")
            release = row.get("release_witness_upper_bound_ns")
            if row.get("schedule") == "cleanup_failure":
                dispatch_result = ((receipt or {}).get("dispatch_result") or {}).get("result", {})
                execution = dispatch_result.get("execution", {})
                if (dispatch_result.get("status") != "execution_failed" or
                        dispatch_result.get("recovery_required") is not True or
                        "INJECTED_RELEASE_PATH_FAILURE" not in execution.get("error", "")):
                    issues.append(f"{identity}:INJECTED_FAILURE_NOT_OBSERVED")
                release = (row.get("supervisor_release") or {}).get("finished_ns")
            if row.get("schedule") == "owner_death":
                release = (row.get("supervisor_release") or {}).get("finished_ns")
                if row.get("worker_returncode", 0) >= 0:
                    issues.append(f"{identity}:WORKER_DEATH_NOT_OBSERVED")
            if release is None or deadline is None:
                issues.append(f"{identity}:RELEASE_WITNESS_OR_DEADLINE_MISSING")
            elif release > deadline + 50_000_000:
                release_violations.append({"case": identity, "deadline_ns": deadline, "release_ns": release, "late_ms": (release - deadline) / 1_000_000})
            if row.get("terminal_key_down") is not False:
                release_violations.append({"case": identity, "terminal_key_down": row.get("terminal_key_down")})

    if hidden:
        decision = "FAIL_SAFETY_GRAPH_HIDDEN_DEPENDENCY"
    elif release_violations:
        decision = "FAIL_SAFETY_RELEASE_LATE_OR_DUPLICATE"
    elif issues:
        decision = "HOLD_SAFETY_GRAPH_EVIDENCE_INCOMPLETE"
    else:
        decision = "PASS_SAFETY_GRAPH_RUNTIME_RECONCILIATION_SCOPED"
    result = {
        "allocation": ALLOCATION, "decision": decision, "case_count": len(raw),
        "issues": issues, "hidden_dependencies": hidden,
        "release_violations": release_violations, "graph_findings": graph_findings,
        "scope": "current-main X11RuntimeSession/X11Backend on pinned local Xvfb/Openbox image; synthetic F8 only",
    }
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision, "issues": len(issues), "hidden": len(hidden), "release_violations": len(release_violations)}, sort_keys=True))
    return 0 if decision.startswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
