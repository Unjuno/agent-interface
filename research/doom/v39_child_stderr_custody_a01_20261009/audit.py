"""Independent audit for the retained child-stderr construction run."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_passed(text, name):
    return any(line.startswith(name + " (") and line.endswith("... ok")
               for line in text.splitlines())


def main():
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    checks = {}
    for name, expected in freeze["source_hashes"].items():
        checks[f"source:{name}"] = sha(REPO / name) == expected
    for name in ("normal-tests.txt", "optimized-tests.txt"):
        text = (HERE / name).read_text()
        checks[f"test_log:{name}:all_pass"] = (
            "Ran 17 tests" in text and "OK" in text and "FAILED" not in text
        )
        checks[f"test_log:{name}:stderr_retention_case"] = test_passed(
            text, "test_failed_session_stderr_is_retained")
        checks[f"test_log:{name}:bounded_reader_case"] = test_passed(
            text, "test_failure_cleanup_bounds_stderr_reader_and_leaves_timed_out_stream_open")
    initial_failure = json.loads((HERE / "AUDIT_INITIAL_FAILURE.json").read_text())
    checks["first_audit_failure_preserved"] = initial_failure["status"] == "FAIL_AUDIT"
    checks["scope:no_live_allocation"] = freeze["scope"]["game_model_vm_gui_invoked"] is False
    result = {
        "schema": "v39-child-stderr-custody-audit-v1",
        "status": "PASS_CONSTRUCTION" if all(checks.values()) else "FAIL_AUDIT",
        "formal_pass": False,
        "checks": checks,
        "scope": "bounded local child-stderr retention only; no live control evidence",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
