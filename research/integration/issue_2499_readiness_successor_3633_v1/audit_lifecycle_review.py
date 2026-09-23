"""Post-formal adversarial check of launched-app lifecycle coverage."""
import hashlib
import json
import sys
from pathlib import Path


def canonical_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def audit(raw_path, out_path):
    raw = json.loads(Path(raw_path).read_text())
    claimed = raw.get("raw_sha256")
    unsigned = dict(raw)
    unsigned.pop("raw_sha256", None)
    digest_ok = canonical_digest(unsigned) == claimed
    launched = {p["app"]: p["pid"] for p in raw.get("processes", [])
                if p.get("app")}
    owners = {app: row.get("pid") for app, row in raw.get("selected", {}).items()}
    cleanup = raw.get("cleanup", {})
    lifecycle = {}
    for app, owner_pid in owners.items():
        launch_pid = launched.get(app)
        cleanup_row = cleanup.get(app, {})
        lifecycle[app] = {
            "window_owner_pid": owner_pid,
            "launch_process_pid": launch_pid,
            "same_pid": owner_pid == launch_pid,
            "tracked_launch_returncode": cleanup_row.get("returncode"),
            "tracked_launch_reaped": cleanup_row.get("reaped"),
            "owner_lifecycle_recorded": owner_pid == launch_pid
        }
    missing = [app for app, row in lifecycle.items()
               if not row["owner_lifecycle_recorded"]]
    if not digest_ok:
        decision = "FAIL_RAW_INTEGRITY"
    elif missing:
        decision = "HOLD_PROCESS_LIFECYCLE_UNVERIFIED"
    elif not cleanup.get("x_socket_absent"):
        decision = "FAIL_X_SERVER_CLEANUP"
    else:
        decision = "PASS_PROCESS_LIFECYCLE_COVERAGE"
    result = {
        "review": "post-formal adversarial lifecycle-coverage check",
        "decision": decision,
        "raw_digest_verified": digest_ok,
        "raw_sha256": claimed,
        "launched_pids": launched,
        "visible_window_owner_pids": owners,
        "process_lifecycle": lifecycle,
        "missing_owner_lifecycle_apps": missing,
        "x_socket_absent": cleanup.get("x_socket_absent"),
        "interpretation": (
            "The GUI identity observations and original raw bytes remain valid, but the frozen cleanup evidence does not follow every visible app owner PID; overall acceptance is HOLD."
            if decision == "HOLD_PROCESS_LIFECYCLE_UNVERIFIED" else decision)
    }
    Path(out_path).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if decision != "FAIL_RAW_INTEGRITY" else 1


if __name__ == "__main__":
    raise SystemExit(audit(sys.argv[1], sys.argv[2]))
