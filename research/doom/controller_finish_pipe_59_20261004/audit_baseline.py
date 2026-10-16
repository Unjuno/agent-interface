"""Independent read-only audit of the single frozen pipe-pressure result."""
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "baseline-run-02"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    result = json.loads((OUT / "result.json").read_text(encoding="utf-8"))
    exit_code = int((OUT / "exit-code.txt").read_text(encoding="ascii").strip())
    checked_hashes = {
        "cleanup_source": digest(ROOT / "source/doom_controller_failure_cleanup_v1.py"),
        "probe": digest(ROOT / "probe_finish_pipe_01.py"),
        "runner": digest(ROOT / "run_baseline.py"),
        "report": digest(ROOT / "REPORT.md"),
        "auditor": digest(Path(__file__)),
    }
    hash_match = checked_hashes == freeze["sha256"]
    checks = {
        "frozen_hashes_match": hash_match,
        "candidate_exit_zero": exit_code == 0,
        "source_hash_bound": result.get("source_sha256") == freeze["sha256"]["cleanup_source"],
        "pipe_filled": type(result.get("pipe_fill_bytes")) is int and result["pipe_fill_bytes"] > 0,
        "cleanup_still_blocked_at_barrier": result.get("blocked_after_barrier") is True,
        "child_alive_at_barrier": result.get("child_alive_at_barrier") is True,
        "planner_not_closed_at_barrier": result.get("planner_closed_at_barrier") is False,
        "primary_exception_preserved": result.get("primary_exception_preserved") is True,
        "external_probe_kill_recorded": (
            result.get("external_cleanup", {}).get("action") == "probe_kill_owned_child" and
            type(result.get("external_cleanup", {}).get("exit_code")) is int),
        "thread_joined_after_external_release": result.get("cleanup_thread_joined") is True,
        "planner_closed_after_external_release": result.get("planner_closed_after_external_release") is True,
        "stderr_captured": (OUT / "stderr.bin").is_file(),
        "stdout_captured": (OUT / "stdout.bin").is_file(),
        "argv_captured": (OUT / "argv.json").is_file(),
    }
    passed = all(checks.values())
    audit = {
        "schema": "doom-controller-finish-pipe-audit-v1",
        "status": "PASS_BASELINE_BLOCK_CONFIRMED" if passed else "FAIL_AUDIT",
        "checks": checks,
        "checked_sha256": checked_hashes,
        "result": result,
        "exit_code": exit_code,
        "scope": "raw-result integrity and frozen boundary assertions; no rerun",
    }
    (OUT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n",
                                    encoding="utf-8")
    print(json.dumps({"status": audit["status"], "checks": checks}, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
