"""Raw-only audit for the current-main versus PR #7429 head comparison."""
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
    if "Ran 7 tests" not in main or "FAILED (failures=1, errors=3)" not in main:
        errors.append("main_expected_3_pass_4_fail_not_observed")
    for evidence in (
        "KeyError: 'input_release_publication'",
        "cannot join thread before it is started",
        "Exception in thread Thread-",
    ):
        if evidence not in main:
            errors.append(f"main_missing:{evidence}")
    if main_exit != "1":
        errors.append(f"main_exit:{main_exit}")
    if "Ran 7 tests" not in pr or "OK" not in pr or "FAILED" in pr:
        errors.append("pr7429_expected_seven_passes_not_observed")
    if pr_exit != "0":
        errors.append(f"pr7429_exit:{pr_exit}")

    return {
        "schema": "map01-executor-v13-main-pr7429-head-c11-audit-v1",
        "decision": "PASS_SCOPED" if not errors else "FAIL_AUDIT",
        "base_main": "911e7b6ec0fba10d9367e45499d13a63232e9434",
        "pr7429_head": "b30fd755e68d470799e6c26f12296a97cf027df8",
        "main_tests": {"passed": 3, "failed": 4, "exit": main_exit},
        "pr7429_tests": {"passed": 7, "failed": 0, "exit": pr_exit},
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
