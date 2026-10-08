"""Versioned read-only reconstruction of retained A04 evidence; never runs candidate code."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUTS = HERE / "inputs"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def verify_input_snapshot(inputs: Path, manifest: dict) -> list[str]:
    errors = []
    for relative, expected in manifest.get("inputs_sha256", {}).items():
        path = inputs / relative
        if not path.is_file():
            errors.append("snapshot input missing: " + relative)
        elif sha256(path.read_bytes()) != expected:
            errors.append("snapshot input hash mismatch: " + relative)
    return errors


def verify_source_snapshot(root: Path, manifest: dict) -> list[str]:
    errors = []
    for relative, expected in manifest.get("source_sha256", {}).items():
        path = root / relative
        if not path.is_file():
            errors.append("audit source missing: " + relative)
        elif sha256(path.read_bytes()) != expected:
            errors.append("audit source hash mismatch: " + relative)
    return errors


def inspect_raw(doc: dict) -> list[str]:
    errors = []
    if doc.get("schema") != "owner-keyup-duplicate-down-result-v1":
        errors.append("result schema")
    if doc.get("runner_error") is not None:
        errors.append("runner error")
    cases = doc.get("cases")
    if not isinstance(cases, list) or len(cases) != 1:
        return errors + ["case count"]
    case = cases[0]
    if (case.get("name"), case.get("identifier"), case.get("step")) != (
        "duplicate_down", "trial-duplicate-down", 13
    ):
        errors.append("case context")
    owner_id = case.get("owner_id")
    token = case.get("intent_token")
    if not isinstance(owner_id, str) or not owner_id or token != "token-duplicate-down":
        errors.append("owner/token identity")
    if case.get("final_down") != []:
        errors.append("fake keymap not neutral")

    records = case.get("owner_records")
    if not isinstance(records, list):
        errors.append("owner record list")
        records = []
    cleanups = [row for row in records if isinstance(row, dict) and row.get("event") == "owner_release"]
    if not any(
        row.get("verified") is True and row.get("keys_down") == [] and row.get("buttons_down") == []
        for row in cleanups
    ):
        errors.append("verified neutral owner cleanup absent")

    events = case.get("events")
    if not isinstance(events, list):
        errors.append("event list")
        events = []
    admissions = [row for row in events if isinstance(row, dict) and row.get("event") == "input_admission"]
    releases = [row for row in events if isinstance(row, dict) and row.get("event") == "input_release_transition"]
    owner_rows = [row for row in records if isinstance(row, dict) and row.get("event") == "owner_keyup"]
    if (len(admissions), len(releases), len(owner_rows)) != (2, 1, 1):
        errors.append("expected two admissions, one release transition, and one owner key-up")

    admission_ids = []
    for sequence, row in enumerate(admissions, start=1):
        expected_id = owner_id + ":admission:" + str(sequence) if isinstance(owner_id, str) else None
        if (row.get("key"), row.get("admission_sequence"), row.get("owner_id"), row.get("admission_id")) != (
            "A", sequence, owner_id, expected_id
        ):
            errors.append("admission key/sequence/id")
        if (row.get("id"), row.get("step"), row.get("intent_token")) != (
            "trial-duplicate-down", 13, token
        ):
            errors.append("admission context")
        admission_ids.append(row.get("admission_id"))
    if len(admission_ids) != 2 or admission_ids[0] == admission_ids[1]:
        errors.append("admissions lack distinct IDs")

    if releases:
        row = releases[0]
        nested = row.get("owner_keyup_receipt")
        if not isinstance(nested, dict):
            errors.append("nested owner receipt absent")
            nested = {}
        latest_id = admission_ids[-1] if admission_ids else None
        if row.get("admission_identity_status") != "ambiguous_multiple_admissions":
            errors.append("ambiguous admission inventory not reported")
        if row.get("owner_keyup_join") != "MATCHED_EXPLICIT_KEYUP":
            errors.append("explicit owner key-up receipt not joined")
        if row.get("admission_id") != latest_id or nested.get("admission_id") != latest_id:
            errors.append("release did not retain latest held-key ID")
        if (row.get("key"), nested.get("key"), nested.get("reason")) != ("A", "A", "explicit_up"):
            errors.append("release key/reason")
        if (row.get("owner_id"), nested.get("owner_id"), row.get("intent_token"), nested.get("intent_token")) != (
            owner_id, owner_id, token, token
        ):
            errors.append("release owner/token identity")
        if (row.get("release_batch_identifier"), row.get("release_batch_step")) != (
            "trial-duplicate-down", 13
        ):
            errors.append("release context")
        if (row.get("release_batch_size"), row.get("release_batch_position")) != (1, 0):
            errors.append("release batch cardinality/position")
        if row.get("physical_verification_authoritative") is not False or row.get("grants_input_authority") is not False:
            errors.append("release authority overclaim")
        if nested.get("physical_verification_authoritative") is not False or nested.get("grants_input_authority") is not False:
            errors.append("owner receipt authority overclaim")
        if nested.get("receipt_id") not in {item.get("receipt_id") for item in owner_rows}:
            errors.append("nested receipt absent from owner history")
        a, b = nested.get("owner_keyup_started_ns"), nested.get("owner_sync_returned_ns")
        c, d = row.get("release_call_started_ns"), row.get("release_call_returned_ns")
        if not (
            nested.get("xsync_completed") is True
            and type(a) is int and type(b) is int and type(c) is int and type(d) is int
            and c <= a <= b <= d
        ):
            errors.append("caller/owner interval nesting")
        if row.get("owner_transition_verified") is not True:
            errors.append("owner batch outcome")

    expected_calls = [
        ["input", 2, 38], ["sync", 1],
        ["input", 2, 38], ["sync", 2],
        ["input", 3, 38], ["sync", 3],
        ["sync", 4],
    ]
    if case.get("calls") != expected_calls:
        errors.append("fake-Xlib call sequence")
    return errors


def source_provenance(inputs: Path) -> dict:
    pre = inputs / "a04-pre-run"
    root_freeze = read_json(pre / "FREEZE.json")
    formal_dir = inputs / "a04-formal"
    formal_freeze = read_json(formal_dir / "FREEZE.json")
    pinned = read_json(inputs / "PINNED_MAIN_TREE.json")
    declared = root_freeze.get("sha256", {})
    root_missing = []
    root_mismatches = []
    for key, expected in declared.items():
        if key.startswith("current_main:"):
            relative = key.removeprefix("current_main:")
            actual = pinned.get("paths", {}).get(relative, {}).get("git_blob")
            if actual != expected:
                root_mismatches.append({"path": "Git blob " + relative, "expected": expected, "actual": actual})
            continue
        path = pre / key
        if not path.is_file():
            root_missing.append({"path": key, "expected_sha256": expected})
        elif sha256(path.read_bytes()) != expected:
            root_mismatches.append({"path": key, "expected": expected, "actual": sha256(path.read_bytes())})

    formal_missing = []
    formal_mismatches = []
    for key, expected in formal_freeze.get("sha256", {}).items():
        if key.startswith("current_main:"):
            relative = key.removeprefix("current_main:")
            actual = pinned.get("paths", {}).get(relative, {}).get("git_blob")
            if actual != expected:
                formal_mismatches.append({"path": "Git blob " + relative, "expected": expected, "actual": actual})
            continue
        path = pre / key
        if not path.is_file():
            formal_missing.append({"path": key, "expected_sha256": expected})
        elif sha256(path.read_bytes()) != expected:
            formal_mismatches.append({"path": key, "expected": expected, "actual": sha256(path.read_bytes())})

    prerun_auditor_sha = sha256((pre / "audit.py").read_bytes())
    formal_auditor_sha = sha256((formal_dir / "FORMAL_AUDIT_SOURCE.py").read_bytes())

    base_copies = {
        "research/doom/doom_retained_input_backend_v4.py": "doom_retained_input_backend_v4_frozen.py",
        "research/live_control/input_owner_v10.py": "input_owner_v10_frozen.py",
        "research/live_control/input_transition_owner_v3.py": "input_transition_owner_v3_frozen.py",
    }
    copy_checks = []
    for source_path, copy_name in base_copies.items():
        copied = (pre / copy_name).read_bytes()
        entry = pinned.get("paths", {}).get(source_path, {})
        computed_blob = hashlib.sha1(b"blob " + str(len(copied)).encode("ascii") + b"\0" + copied).hexdigest()
        copy_checks.append({
            "path": source_path,
            "copied_sha256": sha256(copied),
            "copied_git_blob": computed_blob,
            "pinned_base_git_blob": entry.get("git_blob"),
            "copy_matches_pinned_base": computed_blob == entry.get("git_blob"),
            "freeze_manifest_git_blob": declared.get("current_main:" + source_path),
            "freeze_manifest_matches_base": declared.get("current_main:" + source_path) == entry.get("git_blob"),
        })
    return {
        "main_commit": root_freeze.get("main_commit"),
        "a04_pre_run_source_commit": pinned.get("a04_pre_run_source_commit"),
        "root_freeze_manifest_missing_paths": root_missing,
        "root_freeze_manifest_mismatches": root_mismatches,
        "formal_freeze_manifest_missing_paths": formal_missing,
        "formal_freeze_manifest_mismatches": formal_mismatches,
        "frozen_formal_auditor_source_matches_pre_run_source": formal_auditor_sha == prerun_auditor_sha,
        "formal_auditor_source_sha256": formal_auditor_sha,
        "copied_dependency_checks": copy_checks,
    }


def audit(root: Path = HERE) -> dict:
    inputs = root / "inputs"
    freeze = read_json(root / "A05_FREEZE.json")
    custody_errors = verify_input_snapshot(inputs, freeze) + verify_source_snapshot(root, freeze)
    raw_path = inputs / "a04-formal" / "RESULT.json"
    raw_bytes = raw_path.read_bytes()
    raw = json.loads(raw_bytes)
    raw_errors = inspect_raw(raw)

    formal = inputs / "a04-formal"
    postrun = read_json(formal / "POST_RUN_SHA256.json")
    postrun_mismatches = []
    for name, expected in postrun.items():
        path = formal / name
        actual = sha256(path.read_bytes()) if path.is_file() else None
        if actual != expected:
            postrun_mismatches.append({"path": name, "expected": expected, "actual": actual})

    candidate_exit = (formal / "candidate.exit").read_text(encoding="utf-8").strip()
    audit_exit = (formal / "audit.exit").read_text(encoding="utf-8").strip()
    audit_log = (formal / "audit.log").read_text(encoding="utf-8", errors="replace")
    if candidate_exit != "0":
        custody_errors.append("retained candidate exit is not 0")
    if audit_exit != "1":
        custody_errors.append("retained formal auditor exit is not 1")
    if "FileNotFoundError" not in audit_log or "current_main:" not in audit_log:
        custody_errors.append("retained formal audit log does not show the recorded pre-reconstruction path failure")

    provenance = source_provenance(inputs)
    report = {
        "schema": "owner-keyup-duplicate-down-a05-posthoc-audit-v1",
        "classification": "READ_ONLY_POSTHOC_RECONSTRUCTION_NOT_FORMAL_REAUDIT",
        "input_snapshot_status": "PASS" if not custody_errors else "FAIL",
        "result_sha256": sha256(raw_bytes),
        "postrun_sha256_mismatches": postrun_mismatches,
        "candidate_exit": candidate_exit,
        "original_formal_auditor_exit": audit_exit,
        "raw_reconstruction": "PASS_SCOPED" if not raw_errors else "FAIL_RECONSTRUCTION",
        "raw_base_error_count": len(raw_errors),
        "raw_errors": raw_errors,
        "source_provenance": provenance,
        "formal_allocation_disposition": "STOP_CONSUMED_UNCHANGED",
        "scientific_outcome": "NOT_ASSIGNED_BY_A05",
        "limitations": [
            "A05 is not the consumed formal auditor invocation and does not upgrade A04.",
            "The A04 freeze has Git-blob mismatches and missing local manifest entries; copied dependencies match the declared base commit, but the freeze defects remain STOP evidence.",
            "The trace is fake-Xlib/direct-owner only and has no real X11, physical, application, game, feedback, recovery, latency, safety, or authority interpretation.",
        ],
        "custody_errors": custody_errors,
    }
    return report


if __name__ == "__main__":
    result = audit()
    (HERE / "AUDIT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["input_snapshot_status"] == "PASS" and result["raw_reconstruction"] == "PASS_SCOPED" and not result["postrun_sha256_mismatches"] else 1)
