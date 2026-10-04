"""Raw-only integrity audit for the C10 source-level executor comparison."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit() -> dict:
    pins = json.loads((ROOT / "SOURCE_PINS.json").read_text(encoding="utf-8"))
    errors = []
    for rel, row in pins.items():
        path = ROOT / rel
        if not path.is_file() or sha(path) != row["sha256"]:
            errors.append(f"source_hash:{rel}")

    main = (ROOT / "raw/main-output.txt").read_text(encoding="utf-8")
    pr = (ROOT / "raw/pr7429-output.txt").read_text(encoding="utf-8")
    main_exit = (ROOT / "raw/main-exit.txt").read_text(encoding="utf-8").strip()
    pr_exit = (ROOT / "raw/pr7429-exit.txt").read_text(encoding="utf-8").strip()
    if "Ran 4 tests" not in main or "FAILED (errors=1)" not in main:
        errors.append("main_expected_one_failure_not_observed")
    if "KeyError: 'input_release_publication'" not in main:
        errors.append("main_expected_missing_publication_receipt_not_observed")
    if "release acknowledgement lost" not in main:
        errors.append("main_expected_sink_exception_not_observed")
    if main_exit != "1":
        errors.append(f"main_exit:{main_exit}")
    if "Ran 4 tests" not in pr or "OK" not in pr or "FAILED" in pr:
        errors.append("pr7429_expected_four_passes_not_observed")
    if pr_exit != "0":
        errors.append(f"pr7429_exit:{pr_exit}")

    return {
        "schema": "map01-executor-v13-main-pr7429-sink-error-c10-audit-v1",
        "decision": "PASS_SCOPED" if not errors else "FAIL_AUDIT",
        "base_main": "911e7b6ec0fba10d9367e45499d13a63232e9434",
        "pr7429_head": "5f3e24d3c177bf32f04c9282750f37b413de816b",
        "main_tests": {"passed": 3, "failed": 1, "exit": main_exit},
        "pr7429_tests": {"passed": 4, "failed": 0, "exit": pr_exit},
        "scope": "source-level construction with synthetic backend only",
        "formal_allocation": False,
        "errors": errors,
        "raw_sha256": {
            "main-output.txt": sha(ROOT / "raw/main-output.txt"),
            "pr7429-output.txt": sha(ROOT / "raw/pr7429-output.txt"),
        },
    }


if __name__ == "__main__":
    result = audit()
    (ROOT / "AUDIT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, sort_keys=True))
    if result["errors"]:
        raise SystemExit(1)
