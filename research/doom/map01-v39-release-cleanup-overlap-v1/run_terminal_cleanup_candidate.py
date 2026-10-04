"""Run and retain the focused host candidate suites for terminal cleanup."""
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CASES = (
    ("backend", "research/doom", "test_doom_typed_release_backend_v3", 27),
    ("owner", "research/live_control", "test_input_transition_owner_v3", 8),
    ("wait", "research/doom", "test_overlap_controller_v39_wait", 7),
)
MANIFEST_PATHS = (
    "research/doom/doom_typed_release_backend_v3.py",
    "research/doom/test_doom_typed_release_backend_v3.py",
    "research/doom/map01-v39-release-cleanup-overlap-v1/TERMINAL_BATCH_CLEANUP_EXTENSION_01.md",
    "research/doom/map01-v39-release-cleanup-overlap-v1/run_terminal_cleanup_candidate.py",
    "research/doom/map01-v39-release-cleanup-overlap-v1/run_terminal_cleanup_parent_red.py",
    "research/doom/map01-v39-release-cleanup-overlap-v1/audit_terminal_cleanup_candidate.py",
    "research/doom/map01-v39-release-cleanup-overlap-v1/CANDIDATE_RUN.json",
    "research/doom/map01-v39-release-cleanup-overlap-v1/PARENT_RED.json",
    "research/doom/map01-v39-release-cleanup-overlap-v1/RAW_BACKEND_TESTS.txt",
    "research/doom/map01-v39-release-cleanup-overlap-v1/RAW_OWNER_TESTS.txt",
    "research/doom/map01-v39-release-cleanup-overlap-v1/RAW_WAIT_TESTS.txt",
    "research/doom/map01-v39-release-cleanup-overlap-v1/RAW_PARENT_TERMINAL_RED.txt",
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    result = {
        "schema": "terminal-cleanup-candidate-run-v1",
        "python": sys.version,
        "platform": platform.platform(),
        "source_sha256": {
            "backend": sha256(REPO / "research/doom/doom_typed_release_backend_v3.py"),
            "backend_tests": sha256(REPO / "research/doom/test_doom_typed_release_backend_v3.py"),
        },
        "runs": [],
    }
    for name, directory, module, expected in CASES:
        command = [sys.executable, "-B", "-m", "unittest", "-v", module]
        completed = subprocess.run(
            command, cwd=REPO / directory, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, check=False,
        )
        raw_path = HERE / f"RAW_{name.upper()}_TESTS.txt"
        raw_path.write_text(completed.stdout, encoding="utf-8")
        summary = f"Ran {expected} tests in "
        ok = (
            completed.returncode == 0
            and summary in completed.stdout
            and "\nOK\n" in completed.stdout
            and "FAILED" not in completed.stdout
        )
        result["runs"].append({
            "name": name,
            "command": command,
            "expected_tests": expected,
            "returncode": completed.returncode,
            "raw_file": raw_path.name,
            "raw_sha256": sha256(raw_path),
            "audited_candidate_pass": ok,
        })
        print(f"{name}: rc={completed.returncode}; expected_tests={expected}; PASS={ok}")
    out = HERE / "CANDIDATE_RUN.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = "".join(
        f"{sha256(REPO / path)}  {path}\n" for path in sorted(MANIFEST_PATHS)
    )
    (HERE / "SHA256SUMS.txt").write_text(manifest, encoding="utf-8")
    return 0 if all(row["audited_candidate_pass"] for row in result["runs"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
