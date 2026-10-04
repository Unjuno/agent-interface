"""Raw-only audit for the C12 source-composition construction run."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def has_expected_initial_failure(output: str) -> bool:
    """Bind the retained error to the documented publication-control failure."""
    if ("Ran 7 tests" not in output
            or "FAILED (errors=1)" not in output):
        return False
    error = re.search(
        r"^ERROR: test_cancelled_release_is_published_before_terminal "
        r"\(candidate\.live_control\.test_executor_owner_cancel_cause_v1\."
        r"ExecutorOwnerCancelCauseTests\.test_cancelled_release_is_published_before_terminal\)\n"
        r"(?P<traceback>.*?^StopIteration$)",
        output,
        re.MULTILINE | re.DOTALL,
    )
    if error is None:
        return False
    traceback = error.group("traceback")
    return re.search(
        r'(?m)^    released = next\(row for row in events if row\["event"\] == "input_released"\)$\n'
        r"^ +\^.*$\n"
        r"^StopIteration$",
        traceback,
    ) is not None


def has_exact_owner_derivation(base_source: str, patch_source: str, candidate: str) -> bool:
    """Require the candidate owner to be PR #7441 plus PR #7440's cause recheck."""
    anchor = (
        "            down = [code for code in touched "
        "if bitmap[code // 8] & (1 << (code % 8))]\n"
    )
    addition = (
        "            # Compose PR #7440's final post-I/O cause recheck with PR #7441's key-up receipt.\n"
        "            if reason == 'release' and active is not None and active.cancel.is_set():\n"
        "                reason = 'cancelled'\n"
    )
    patch_logic = (
        "            if reason == 'release' and active is not None and active.cancel.is_set():\n"
        "                reason = 'cancelled'\n"
    )
    return (
        base_source.count(anchor) == 1
        and patch_logic in patch_source
        and candidate == base_source.replace(anchor, anchor + addition, 1)
    )


def has_pinned_owner_sources(pins: dict, freeze: dict) -> bool:
    derivation = freeze["candidate_derivation"]
    expected = {
        derivation["base_path"]: freeze["pr7441_head"],
        derivation["patch_source"]: freeze["pr7440_head"],
    }
    return all(
        path in pins
        and pins[path].get("source_ref") == source_ref
        and re.fullmatch(r"[0-9a-f]{64}", pins[path].get("sha256", ""))
        for path, source_ref in expected.items()
    )


def main() -> None:
    pins = json.loads((ROOT / "SOURCE_PINS.json").read_text(encoding="utf-8"))
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    errors = []
    for rel, expected in pins.items():
        path = ROOT / rel
        if not path.is_file() or sha(path) != expected["sha256"]:
            errors.append(f"source_hash:{rel}")

    derivation = freeze["candidate_derivation"]
    base_path = derivation["base_path"]
    patch_path = derivation["patch_source"]
    owner_sources_pinned = has_pinned_owner_sources(pins, freeze)
    if not owner_sources_pinned:
        errors.append("owner_derivation_inputs_not_pinned")
    owner_derivation_passed = False
    try:
        base_source = (ROOT / base_path).read_text(encoding="utf-8")
        patch_source = (ROOT / patch_path).read_text(encoding="utf-8")
        candidate_owner = (ROOT / "candidate/live_control/input_owner_v12.py").read_text(
            encoding="utf-8"
        )
        owner_derivation_passed = has_exact_owner_derivation(
            base_source, patch_source, candidate_owner
        )
        if not owner_derivation_passed:
            errors.append("candidate_owner_not_exact_frozen_derivation")
    except OSError:
        errors.append("owner_derivation_source_missing")

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
    if not has_expected_initial_failure(initial):
        errors.append("initial_combined_process_failure_not_retained_as_documented")
    if initial_exit != "1":
        errors.append(f"initial_combined_process_exit:{initial_exit}")

    result = {
        "schema": "map01-cancel-keyup-receipt-composition-c12-audit-v1",
        "decision": "PASS_COMPOSITION_SCOPED" if not errors else "FAIL_AUDIT",
        "test_count": 7,
        "composition_tests_passed": 6 if " ... ok" in composition else 0,
        "owner_sources_pinned": owner_sources_pinned,
        "owner_derivation_passed": owner_derivation_passed,
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
