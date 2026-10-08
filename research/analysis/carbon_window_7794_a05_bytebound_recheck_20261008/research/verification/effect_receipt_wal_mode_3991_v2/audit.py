from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import tempfile
from pathlib import Path

MODES = ("DELETE", "WAL")
PROTOCOLS = ("EFFECT_FIRST", "RECEIPT_FIRST", "ATOMIC_LOCAL", "ATOMIC_EXTERNAL")
CUTS = ("BEFORE", "AFTER_FIRST", "AFTER_SECOND", "AFTER_COMMIT", "NORMAL")
CONTROLS = ("ALTERED_OPERATION_CONTENT", "WRONG_SESSION", "WRONG_RESOURCE", "WRONG_EPOCH", "BOOL_AS_INTEGER")


def expected_counts(protocol: str, cut: str) -> tuple[int, int, bool]:
    if protocol == "RECEIPT_FIRST" and cut == "AFTER_FIRST":
        return 0, 1, False
    if protocol in ("EFFECT_FIRST", "ATOMIC_EXTERNAL") and cut == "AFTER_FIRST":
        return 2, 1, True
    retry = cut in ("BEFORE", "AFTER_FIRST", "AFTER_SECOND") and not (
        protocol == "RECEIPT_FIRST" and cut == "AFTER_FIRST"
    )
    return 1, 1, retry


def _query_counts(snapshot_dir: Path, protocol: str) -> tuple[int, int]:
    with tempfile.TemporaryDirectory() as td:
        copied = Path(td)
        for p in snapshot_dir.iterdir():
            if p.is_file() and p.name != "MANIFEST.json":
                shutil.copyfile(p, copied / p.name)
        effect_db = copied / "effect.sqlite"
        receipt_db = effect_db if protocol != "ATOMIC_EXTERNAL" else copied / "receipt.sqlite"
        with sqlite3.connect(f"file:{effect_db}?mode=ro", uri=True) as db:
            effects = db.execute("SELECT count(*) FROM effects").fetchone()[0]
        with sqlite3.connect(f"file:{receipt_db}?mode=ro", uri=True) as db:
            receipts = db.execute("SELECT count(*) FROM receipts").fetchone()[0]
        return effects, receipts


def _check_snapshot(case_dir: Path, stage: str, declared: dict) -> bool:
    folder = case_dir / stage
    manifest_path = folder / "MANIFEST.json"
    if not manifest_path.is_file():
        return False
    manifest = json.loads(manifest_path.read_text())
    if manifest != declared:
        return False
    for name, entry in manifest.items():
        path = folder / name
        if not path.is_file() or path.stat().st_size != entry["bytes"]:
            return False
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            return False
    return True


def audit_result(result: dict, raw_root: Path) -> dict:
    errors: list[str] = []
    rows = result.get("formal_rows", [])
    controls = result.get("control_rows", [])
    construction = result.get("kind") == "CONSTRUCTION_EXCLUDED"
    reps = (0,) if construction else (1, 2, 3)
    expected_keys = {
        f"{mode}-{protocol}-{cut}-r{rep}"
        for mode in MODES for protocol in PROTOCOLS for cut in CUTS for rep in reps
    }
    if result.get("kind") not in ("FORMAL", "CONSTRUCTION_EXCLUDED") or result.get("invocations") != 1:
        errors.append("formal_identity_or_invocation")
    keys = [row.get("case_id") for row in rows]
    if len(rows) != 120 or len(set(keys)) != 120 or set(keys) != expected_keys:
        errors.append("formal_matrix_incomplete_or_duplicate")
    control_keys_expected = {
        f"{mode}-INVALID-{kind}-r{rep}"
        for mode in MODES for kind in CONTROLS for rep in reps
    }
    control_keys = [row.get("case_id") for row in controls]
    if len(controls) != 30 or len(set(control_keys)) != 30 or set(control_keys) != control_keys_expected:
        errors.append("control_matrix_incomplete_or_duplicate")

    for row in rows:
        mode, protocol, cut = row.get("mode"), row.get("protocol"), row.get("cut")
        case_id = row.get("case_id", "")
        if mode not in MODES or protocol not in PROTOCOLS or cut not in CUTS:
            errors.append(f"invalid_dimensions:{case_id}")
            continue
        effect_expected, receipt_expected, retry_expected = expected_counts(protocol, cut)
        rc_expected = 0 if cut == "NORMAL" else 73
        if row.get("child_returncode") != rc_expected:
            errors.append(f"child_returncode:{case_id}")
        if row.get("status_returncode") != 0:
            errors.append(f"status_returncode:{case_id}")
        try:
            status = json.loads(row.get("status_stdout", ""))
        except Exception:
            status = {}
        status_expected = "NOT_FOUND" if retry_expected else "COMPLETED"
        if status.get("status") != status_expected or status.get("effect_access") is not False:
            errors.append(f"receipt_only_status:{case_id}")
        if row.get("retry_authorized") is not retry_expected or row.get("retry_count") != int(retry_expected):
            errors.append(f"retry_policy:{case_id}")
        rp = row.get("retry_process")
        if retry_expected and (not isinstance(rp, dict) or rp.get("returncode") != 0):
            errors.append(f"retry_exit:{case_id}")
        if not retry_expected and rp is not None:
            errors.append(f"unexpected_retry:{case_id}")
        if row.get("effect_count_after_retry") != effect_expected or row.get("receipt_count_after_retry") != receipt_expected:
            errors.append(f"recorded_counts:{case_id}")
        case_dir = raw_root / case_id
        if not _check_snapshot(case_dir, "PRE_RECOVERY", row.get("pre_recovery_files", {})):
            errors.append(f"pre_recovery_bytes:{case_id}")
        if not _check_snapshot(case_dir, "POST_RECOVERY", row.get("post_recovery_files", {})):
            errors.append(f"post_recovery_bytes:{case_id}")
        try:
            counts = _query_counts(case_dir / "POST_RECOVERY", protocol)
            if counts != (effect_expected, receipt_expected):
                errors.append(f"raw_database_state:{case_id}")
        except Exception as exc:
            errors.append(f"raw_database_read:{case_id}:{type(exc).__name__}")

    for row in controls:
        case_id = row.get("case_id", "")
        if row.get("accepted") is not False or row.get("effect_count") != 0 or row.get("receipt_count") != 0:
            errors.append(f"identity_control_effect:{case_id}")
        if row.get("refusal") != "IDENTITY_OR_TYPE_MISMATCH":
            errors.append(f"identity_control_refusal:{case_id}")
        case_dir = raw_root / case_id
        if not _check_snapshot(case_dir, "BEFORE_CONTROL", row.get("before_files", {})):
            errors.append(f"control_before_bytes:{case_id}")
        if not _check_snapshot(case_dir, "AFTER_CONTROL", row.get("after_files", {})):
            errors.append(f"control_after_bytes:{case_id}")
        if row.get("before_files") != row.get("after_files"):
            errors.append(f"control_mutated_store:{case_id}")

    return {"schema": "effect-receipt-independent-raw-audit-v1",
            "decision": ("PASS_CONSTRUCTION_AUDIT" if construction else "PASS_JOURNAL_MODE_TRANSACTION_SCOPE_SCOPED") if not errors else "HOLD_AUDIT_INTEGRITY",
            "formal_rows": len(rows), "control_rows": len(controls), "errors": errors,
            "effect_first_after_first_duplicates": sum(r.get("protocol") == "EFFECT_FIRST" and r.get("cut") == "AFTER_FIRST" and r.get("effect_count_after_retry") == 2 for r in rows),
            "atomic_external_after_first_duplicates": sum(r.get("protocol") == "ATOMIC_EXTERNAL" and r.get("cut") == "AFTER_FIRST" and r.get("effect_count_after_retry") == 2 for r in rows),
            "receipt_first_false_completed": sum(r.get("protocol") == "RECEIPT_FIRST" and r.get("cut") == "AFTER_FIRST" and r.get("effect_count_after_retry") == 0 and r.get("receipt_count_after_retry") == 1 for r in rows),
            "atomic_local_exactly_once": sum(r.get("protocol") == "ATOMIC_LOCAL" and r.get("effect_count_after_retry") == 1 and r.get("receipt_count_after_retry") == 1 for r in rows)}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = audit_result(json.loads(args.result.read_text()), args.raw_root)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if report["decision"] == "PASS_JOURNAL_MODE_TRANSACTION_SCOPE_SCOPED" else 1)
