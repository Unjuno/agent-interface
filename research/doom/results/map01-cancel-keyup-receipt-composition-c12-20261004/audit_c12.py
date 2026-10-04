"""Raw-only audit for the C12 source-composition construction run."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    pins = json.loads((ROOT / "SOURCE_PINS.json").read_text(encoding="utf-8"))
    errors = []
    for rel, expected in pins.items():
        path = ROOT / rel
        if not path.is_file() or sha(path) != expected["sha256"]:
            errors.append(f"source_hash:{rel}")

    composition = (ROOT / "raw/composition-output.txt").read_text(encoding="utf-8")
    composition_exit = (ROOT / "raw/composition-exit.txt").read_text(encoding="utf-8").strip()
    control = (ROOT / "raw/publication-control-output.txt").read_text(encoding="utf-8")
    control_exit = (ROOT / "raw/publication-control-exit.txt").read_text(encoding="utf-8").strip()
    initial = (ROOT / "raw/initial-combined-suite-output.txt").read_text(encoding="utf-8")
    initial_exit = (ROOT / "raw/initial-combined-suite-exit.txt").read_text(encoding="utf-8").strip()
    tests = (
        "test_explicit_keyup_receipt_and_post_io_cancel_cause_coexist",
        "test_partial_release_batch_is_discarded_on_step_exception",
        "test_release_batch_preserves_backend_v2_program_step_provenance",
        "test_duplicate_second_owner_history_row_fails_closed",
        "test_missing_second_owner_history_row_fails_closed",
        "test_two_key_receipts_keep_identity_order_and_distinct_bounds",
    )
    for test in tests:
        if test not in composition:
            errors.append(f"test_not_passed:{test}")
    if ("Ran 6 tests" not in composition or "OK" not in composition
            or "FAILED" in composition or composition.count(" ... ok") != 6):
        errors.append("six_test_composition_suite_not_clean")
    if composition_exit != "0":
        errors.append(f"composition_exit:{composition_exit}")
    if not re.search(
        r"^test_cancelled_release_is_published_before_terminal \(.*\) \.\.\. ok$",
        control, re.MULTILINE
    ) or "Ran 1 test" not in control or "OK" not in control or "FAILED" in control:
        errors.append("isolated_publication_control_not_clean")
    if control_exit != "0":
        errors.append(f"publication_control_exit:{control_exit}")
    if "Ran 7 tests" not in initial or "FAILED (errors=1)" not in initial or "StopIteration" not in initial:
        errors.append("initial_combined_process_failure_not_retained_as_documented")
    if initial_exit != "1":
        errors.append(f"initial_combined_process_exit:{initial_exit}")

    result = {
        "schema": "map01-cancel-keyup-receipt-composition-c12-audit-v1",
        "decision": "PASS_COMPOSITION_SCOPED" if not errors else "FAIL_AUDIT",
        "test_count": 7,
        "composition_tests_passed": 6 if " ... ok" in composition else 0,
        "publication_control_passed": control_exit == "0",
        "composition_exit": composition_exit,
        "publication_control_exit": control_exit,
        "raw_sha256": {
            "composition-output.txt": sha(ROOT / "raw/composition-output.txt"),
            "publication-control-output.txt": sha(ROOT / "raw/publication-control-output.txt"),
            "initial-combined-suite-output.txt": sha(ROOT / "raw/initial-combined-suite-output.txt"),
        },
        "source_count": len(pins),
        "formal_or_live_allocation": False,
        "scope": "host synthetic software construction",
        "errors": errors,
    }
    (ROOT / "AUDIT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
