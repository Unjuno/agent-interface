"""Check frozen V39 recovery replay inputs and outputs."""
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
TRACE = ROOT / "research/doom/results/map01-v39-coast-liveness-live-01"
FILES = {
    "test": BASE / "test_live_trace_pair_recovery.py",
    "finding": BASE / "PAIR_RECOVERY_FINDING.md",
    "controller": BASE / "source/pair_recovery/map01_overlap_controller_v39.py",
    "guard": BASE / "source/pair_recovery/observable_signal_guard_v2.py",
    "raw_trace": TRACE / "runtime/events.jsonl",
    "report": TRACE / "report.json",
    "replay_output": BASE / "out/pair-recovery-replay.txt",
    "replay_exit": BASE / "out/pair-recovery-replay-exit.txt",
    "related_tests_exit": BASE / "out/pair-recovery-related-tests-exit.txt",
    "related_tests_output": BASE / "out/pair-recovery-related-tests.txt",
}
EXPECTED = {
    "controller": "704c8c8a35f88765f207e4be18b4e32979fdcb6960aaea fcb867dcee4cb8eed0".replace(" ", ""),
    "guard": "7be055c4bd68a1528f4b2b02b543435bd64465ea42d4452f5597d6dce08442a0",
    "raw_trace": "2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381",
    "report": "719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    for label, path in FILES.items():
        if not path.is_file():
            raise SystemExit(f"FAIL missing {label}: {path}")
    for label, digest in EXPECTED.items():
        actual = sha(FILES[label])
        if actual != digest:
            raise SystemExit(f"FAIL {label} sha256 {actual} != {digest}")
    if FILES["replay_exit"].read_text().strip() != "0":
        raise SystemExit("FAIL replay exit code")
    output = FILES["replay_output"].read_text()
    if "Ran 1 test" not in output or "OK" not in output:
        raise SystemExit("FAIL replay output is not a passing one-test run")
    related_output = FILES["related_tests_output"].read_text()
    if (FILES["related_tests_exit"].read_text().strip() != "0" or
            "Ran 43 tests" not in related_output or "OK" not in related_output):
        raise SystemExit("FAIL related V39 test output is not a passing 43-test run")
    report = json.loads(FILES["report"].read_text(encoding="utf-8"))
    decision = next(row for row in report["decisions"] if row.get("iteration") == 5)
    if decision["cover_validity_admission"]["effective"]["hard_minimum"] != 51:
        raise SystemExit("FAIL historical threshold")
    if decision["policy_invalidation"]["sequence"] != 218:
        raise SystemExit("FAIL historical invalidation sequence")
    print("PAIR RECOVERY AUDIT PASS")
    for label, path in FILES.items():
        print(f"{label}: {path.relative_to(ROOT)} {sha(path)}")


if __name__ == "__main__":
    main()
