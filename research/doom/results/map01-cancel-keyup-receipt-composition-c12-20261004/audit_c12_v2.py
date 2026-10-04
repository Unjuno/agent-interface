"""Additive manifest-bound audit for the retained C12 construction outputs."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(root: Path = ROOT) -> dict:
    manifest = json.loads((root / "RUN_V2.json").read_text(encoding="utf-8"))
    errors: list[str] = []
    expected_manifest = {
        "schema": "map01-cancel-keyup-receipt-composition-c12-run-v2",
        "supersedes_manifest": "RUN.json",
        "working_directory": ".",
        "command": ["python", "-B", "run_c12.py"],
        "composition_test_count": 6,
        "isolated_control_test_count": 1,
        "test_count": 7,
        "source_pins": "SOURCE_PINS.json",
        "source_pins_sha256": "d321adfc9cd5de98640f04b8faaf0e2a6f7571d5a6a8891c12c5ee1ce0113b6b",
        "composition_output": "raw/composition-output.txt",
        "composition_exit_receipt": "raw/composition-exit.txt",
        "publication_control_output": "raw/publication-control-output.txt",
        "publication_control_exit_receipt": "raw/publication-control-exit.txt",
        "initial_combined_output": "raw/initial-combined-suite-output.txt",
        "initial_combined_exit_receipt": "raw/initial-combined-suite-exit.txt",
        "expected_exit_values": {
            "composition_exit_receipt": "0",
            "publication_control_exit_receipt": "0",
            "initial_combined_exit_receipt": "1",
        },
    }
    if manifest != expected_manifest:
        errors.append("run_manifest_contract_mismatch")

    pins_path = root / "SOURCE_PINS.json"
    pins: dict = {}
    if not pins_path.is_file() or sha(pins_path) != expected_manifest["source_pins_sha256"]:
        errors.append("source_pins_manifest_hash")
    else:
        pins = json.loads(pins_path.read_text(encoding="utf-8"))
        for rel, record in pins.items():
            candidate = Path(rel)
            path = root / candidate
            if candidate.is_absolute() or ".." in candidate.parts or not path.is_file():
                errors.append(f"source_pin_path:{rel}")
            elif not isinstance(record, dict) or sha(path) != record.get("sha256"):
                errors.append(f"source_pin_hash:{rel}")

    fields = {
        "composition_output": "composition-output.txt",
        "publication_control_output": "publication-control-output.txt",
        "initial_combined_output": "initial-combined-suite-output.txt",
        "composition_exit_receipt": "composition-exit.txt",
        "publication_control_exit_receipt": "publication-control-exit.txt",
        "initial_combined_exit_receipt": "initial-combined-suite-exit.txt",
    }
    paths: dict[str, Path] = {}
    for field, expected_name in fields.items():
        rel = manifest.get(field)
        if not isinstance(rel, str) or rel != f"raw/{expected_name}" or Path(rel).is_absolute() or ".." in Path(rel).parts:
            errors.append(f"manifest_path:{field}")
            continue
        path = root / rel
        if not path.is_file():
            errors.append(f"missing_manifest_member:{field}")
        else:
            paths[field] = path

    for field, path in paths.items():
        if field.endswith("exit_receipt"):
            actual = path.read_text(encoding="utf-8").strip()
            expected = manifest["expected_exit_values"].get(field)
            if actual != expected:
                errors.append(f"exit_receipt_value:{field}")

    composition = paths.get("composition_output")
    if composition:
        text = composition.read_text(encoding="utf-8")
        tests = (
            "test_explicit_keyup_receipt_and_post_io_cancel_cause_coexist",
            "test_partial_release_batch_is_discarded_on_step_exception",
            "test_release_batch_preserves_backend_v2_program_step_provenance",
            "test_duplicate_second_owner_history_row_fails_closed",
            "test_missing_second_owner_history_row_fails_closed",
            "test_two_key_receipts_keep_identity_order_and_distinct_bounds",
        )
        for test in tests:
            if test not in text:
                errors.append(f"test_not_passed:{test}")
        if "Ran 6 tests" not in text or "OK" not in text or "FAILED" in text or text.count(" ... ok") != 6:
            errors.append("six_test_composition_suite_not_clean")

    control = paths.get("publication_control_output")
    if control:
        text = control.read_text(encoding="utf-8")
        if not re.search(r"^test_cancelled_release_is_published_before_terminal \(.*\) \.\.\. ok$", text, re.MULTILINE) or "Ran 1 test" not in text or "OK" not in text or "FAILED" in text:
            errors.append("isolated_publication_control_not_clean")

    initial = paths.get("initial_combined_output")
    if initial:
        text = initial.read_text(encoding="utf-8")
        if "Ran 7 tests" not in text or "FAILED (errors=1)" not in text or "StopIteration" not in text:
            errors.append("initial_failure_not_retained_as_documented")

    return {
        "schema": "map01-cancel-keyup-receipt-composition-c12-audit-v2",
        "decision": "PASS_COMPOSITION_SCOPED" if not errors else "FAIL_AUDIT",
        "manifest": "RUN_V2.json",
        "manifest_sha256": sha(root / "RUN_V2.json"),
        "source_count": len(pins),
        "raw_sha256": {field: sha(path) for field, path in paths.items()},
        "formal_or_live_allocation": False,
        "scope": "host-side synthetic software construction",
        "errors": errors,
    }


def main() -> None:
    result = audit()
    (ROOT / "AUDIT_V2.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if result["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
