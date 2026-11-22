"""Independent audit for the text-mode follow-up baseline."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT.parent
OUT = ROOT / "run-01"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    paths = {
        "preregistration": ROOT / "PREREGISTRATION.md",
        "probe": ROOT / "probe.py",
        "runner": ROOT / "run_probe.py",
        "auditor": Path(__file__),
        "source": PACKAGE / "source/doom_controller_failure_cleanup_v1.py",
    }
    hashes = {name: digest(path) for name, path in paths.items()}
    result = json.loads((OUT / "result.json").read_text(encoding="utf-8"))
    receipt = json.loads((OUT / "controller-failure.json").read_text(encoding="utf-8"))
    checks = {
        "frozen_hashes_match": hashes == freeze["sha256"],
        "runner_exit_zero": (OUT / "exit-code.txt").read_text(encoding="ascii").strip() == "0",
        "text_mode_enabled": result.get("stdin_text_mode") is True,
        "pipe_filled": type(result.get("pipe_fill_bytes")) is int and result["pipe_fill_bytes"] > 0,
        "blocked_at_half_second_barrier": result.get("blocked_after_barrier") is True,
        "child_alive_at_barrier": result.get("child_alive_at_barrier") is True,
        "planner_open_at_barrier": result.get("planner_closed_at_barrier") is False,
        "external_probe_kill_recorded": result.get("external_cleanup", {}).get("action") == "probe_kill_owned_child",
        "cleanup_thread_joined": result.get("cleanup_thread_joined") is True,
        "planner_closed_after_release": result.get("planner_closed_after_external_release") is True,
        "primary_exception_preserved": result.get("primary_exception_preserved") is True,
        "no_probe_thread_error": result.get("cleanup_thread_error") is None,
        "finish_failed_only_after_pipe_release": any(
            row.get("stage") == "finish_send" and row.get("status") == "failed" and
            row.get("error_type") == "BrokenPipeError" for row in receipt.get("stages", [])),
        "receipt_child_retired": type(receipt.get("child_exit_code")) is int,
        "stdout_captured": (OUT / "stdout.bin").is_file(),
        "stderr_captured": (OUT / "stderr.bin").is_file(),
        "argv_captured": (OUT / "argv.json").is_file(),
    }
    report = {
        "allocation": "MAP01-CONTROLLER-FINISH-PIPE-FOLLOWUP-01-20261005",
        "status": "PASS_TEXT_MODE_PIPE_BLOCK_CONFIRMED" if all(checks.values()) else "FAIL_AUDIT",
        "checks": checks,
        "checked_sha256": hashes,
        "finish_send_error_type": next((row.get("error_type") for row in receipt.get("stages", [])
                                         if row.get("stage") == "finish_send"), None),
        "scope": "one corrected text-mode synthetic pipe-pressure boundary probe",
    }
    (OUT / "audit.json").write_text(json.dumps(report, indent=2) + "\n",
                                     encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
