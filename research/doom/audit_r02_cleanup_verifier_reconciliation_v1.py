"""Reconcile the retained r02 cleanup receipt against its frozen source and raw rows.

This is a read-only posthoc audit. It never launches a game, model, Docker,
GUI, or input operation, and it does not rewrite the retained allocation.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ALLOCATION = ROOT / "research/doom/map01-v39-current-main-threat-live-20261024-r02"
OUT = ROOT / "research/doom/results/r02_cleanup_verifier_reconciliation_20261104/audit.json"
CURRENT_CLEANUP = ROOT / "research/doom/doom_controller_failure_cleanup_v1.py"


def fail(message: str) -> None:
    raise RuntimeError(message)


def canonical_text_bytes(path: Path) -> bytes:
    raw = path.read_bytes()
    if b"\r" in raw.replace(b"\r\n", b""):
        fail(f"unexpected bare CR in text evidence: {path}")
    return raw.replace(b"\r\n", b"\n")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_bytes(revision: str, path: str) -> bytes:
    return subprocess.check_output(
        ["git", "-C", str(ROOT), "show", f"{revision}:{path}"]
    )


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    prereg_path = ALLOCATION / "PREREG.json"
    lineage_path = ALLOCATION / "KEY_LINEAGE_AUDIT_V1.json"
    failure_path = ALLOCATION / "raw/controller-failure.json"
    events_path = ALLOCATION / "raw/runtime/events.jsonl"
    owners_path = ALLOCATION / "raw/runtime/owner-events.json"
    score_path = ALLOCATION / "raw/runtime/score.json"
    samples_path = ALLOCATION / "raw/runtime/scorer-samples.jsonl"

    prereg = read_json(prereg_path)
    lineage = read_json(lineage_path)
    failure = read_json(failure_path)
    owner_rows = read_json(owners_path)
    score = read_json(score_path)

    lineage_auditor_rel = "research/doom/audit_map01_v39_retained_key_lineage_v1.py"
    lineage_auditor_bytes = (ROOT / lineage_auditor_rel).read_bytes()
    lineage_auditor_lf_sha = sha256(lineage_auditor_bytes.replace(b"\r\n", b"\n"))
    lineage_auditor_crlf_sha = sha256(
        lineage_auditor_bytes.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    )
    if lineage.get("audit_code_sha256") not in {lineage_auditor_lf_sha, lineage_auditor_crlf_sha}:
        fail("retained key-lineage auditor source identity mismatch")

    commit = prereg["repository_commit"]
    cleanup_rel = "research/doom/doom_controller_failure_cleanup_v1.py"
    frozen_cleanup = git_bytes(commit, cleanup_rel)
    current_cleanup_rel = "research/doom/doom_controller_failure_cleanup_v1.py"
    current_cleanup_blob = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", f"HEAD:{current_cleanup_rel}"]
    ).decode("ascii").strip()
    if subprocess.check_output(
        ["git", "-C", str(ROOT), "status", "--porcelain", "--", current_cleanup_rel]
    ).strip():
        fail("current cleanup verifier has uncommitted worktree changes")

    expected_frozen_sha = prereg["runtime_source_sha256"][cleanup_rel]
    frozen_lf_sha = sha256(frozen_cleanup)
    frozen_crlf_sha = sha256(frozen_cleanup.replace(b"\n", b"\r\n"))
    if expected_frozen_sha not in {frozen_lf_sha, frozen_crlf_sha}:
        fail("frozen cleanup source does not match preregistered LF/CRLF identity")

    old_pattern = re.compile(
        rb"all\(\s*type\(row\) is dict and row\.get\('verified'\) is True\s+"
        rb"for row in owner_rows\s*\)"
    )
    if old_pattern.search(frozen_cleanup) is None:
        fail("frozen source lacks the historical generic-verified owner predicate")

    # Load the exact current-main helper from this clean source checkout.
    spec = importlib.util.spec_from_file_location("r02_current_cleanup", CURRENT_CLEANUP)
    if spec is None or spec.loader is None:
        fail("could not load current cleanup verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    old_closed = (
        type(owner_rows) is list
        and bool(owner_rows)
        and type(owner_rows[-1]) is dict
        and owner_rows[-1].get("event") == "owner_release"
        and owner_rows[-1].get("reason") == "close"
        and all(type(row) is dict and row.get("verified") is True for row in owner_rows)
    )
    current_row_results = [bool(module.owner_event_verified(row)) for row in owner_rows]
    current_closed = (
        type(owner_rows) is list
        and bool(owner_rows)
        and type(owner_rows[-1]) is dict
        and owner_rows[-1].get("event") == "owner_release"
        and owner_rows[-1].get("reason") == "close"
        and all(current_row_results)
    )

    stage_rows = failure.get("stages", [])
    stage_results = {row.get("stage"): row for row in stage_rows if type(row) is dict}
    non_owner_components = {
        "child_exit": failure.get("child_exit_code") is not None,
        "planner_close_returned": stage_results.get("planner_close", {}).get("status") == "returned",
        "stdout_reader_retired": failure.get("stdout_reader_retired") is True,
        "stdout_reader_error_free": failure.get("stdout_reader_errors") == [],
        "input_terminals_complete": failure.get("input_terminals_complete") is True,
        "empty_release_verified": failure.get("input_releases_verified_empty") is True,
        "scorer_terminal_observed": failure.get("scorer_terminal_observed") is True,
        "score_file_present": failure.get("score_file_present") is True and score_path.is_file(),
        "all_cleanup_stages_returned": bool(stage_rows) and all(
            row.get("status") == "returned" for row in stage_rows
        ),
    }

    expected_hashes = lineage["evidence_sha256"]
    evidence_paths = {
        "PREREG.json": prereg_path,
        "events.jsonl": events_path,
        "owner-events.json": owners_path,
        "score.json": score_path,
        "scorer-samples.jsonl": samples_path,
    }
    evidence_hash_audit = {}
    for name, path in evidence_paths.items():
        canonical = canonical_text_bytes(path)
        lf_digest = sha256(canonical)
        crlf_digest = sha256(canonical.replace(b"\n", b"\r\n"))
        if expected_hashes[name] not in {lf_digest, crlf_digest}:
            fail(f"retained evidence hash mismatch for {name}: LF={lf_digest}, CRLF={crlf_digest}")
        matched_representation = "LF" if expected_hashes[name] == lf_digest else "CRLF"
        evidence_hash_audit[name] = {
            "canonical_lf_sha256": lf_digest,
            "canonical_crlf_sha256": crlf_digest,
            "working_tree_byte_sha256": sha256(path.read_bytes()),
            "expected_sha256": expected_hashes[name],
            "matches_representation": matched_representation,
        }

    if not all(non_owner_components.values()):
        fail(f"unexpected non-owner cleanup component failure: {non_owner_components}")
    if old_closed or failure.get("owner_events_closed") is not False:
        fail("retained old verifier outcome does not reproduce")
    if failure.get("cleanup_complete") is not False:
        fail("retained cleanup_complete=false was not preserved")
    if current_closed is not True or not all(current_row_results):
        fail("current event-specific verifier did not accept every retained owner row")
    if len(owner_rows) != 10 or sum(row.get("event") == "owner_explicit_keyup" for row in owner_rows) != 4:
        fail("unexpected retained owner-event shape")
    generic_verified_count = sum(row.get("verified") is True for row in owner_rows)
    if generic_verified_count != 6:
        fail(f"unexpected generic-verified owner-event count: {generic_verified_count}")
    if lineage.get("pass") is not True or lineage.get("verified_key_release_count") != 5:
        fail("retained key-lineage audit no longer matches its stated PASS")

    prereg_hash_file = (ALLOCATION / "PREREG.sha256").read_text(encoding="ascii").split()[0]
    if prereg_hash_file != expected_hashes["PREREG.json"]:
        fail("PREREG.sha256 disagrees with retained lineage manifest")

    result = {
        "schema": "map01-v39-r02-cleanup-verifier-reconciliation-v1",
        "classification": "RETAINED_CLEANUP_FALSE_NEGATIVE_RECONCILED",
        "allocation_id": prereg["allocation_id"],
        "frozen_repository_commit": commit,
        "frozen_cleanup_source_sha256_lf": frozen_lf_sha,
        "frozen_cleanup_source_sha256_crlf": frozen_crlf_sha,
        "preregistered_cleanup_source_sha256": expected_frozen_sha,
        "current_main_commit": subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"]
        ).decode("ascii").strip(),
        "current_cleanup_source_git_blob": current_cleanup_blob,
        "retained_key_lineage_auditor_source_sha256": lineage.get("audit_code_sha256"),
        "old_generic_owner_predicate_closed": old_closed,
        "old_owner_events_closed_receipt": failure["owner_events_closed"],
        "current_event_specific_owner_rows_valid": all(current_row_results),
        "current_owner_events_closed_recomputed": current_closed,
        "owner_event_count": len(owner_rows),
        "explicit_keyup_count": sum(row.get("event") == "owner_explicit_keyup" for row in owner_rows),
        "generic_verified_count": sum(row.get("verified") is True for row in owner_rows),
        "last_owner_event": {
            "event": owner_rows[-1].get("event"),
            "reason": owner_rows[-1].get("reason"),
            "verified": owner_rows[-1].get("verified"),
        },
        "non_owner_cleanup_components": non_owner_components,
        "retained_cleanup_complete": failure["cleanup_complete"],
        "retained_runtime_failure": {
            "type": failure.get("primary_error_type"),
            "stage": failure.get("failed_stage"),
            "message_retained": "primary_error_message" in failure,
        },
        "retained_task_effect": lineage["task_effect"],
        "retained_score": {
            "map_exit": score.get("map_exit"),
            "death_count": score.get("death_count"),
            "kill_count": score.get("kill_count"),
        },
        "evidence_hashes": evidence_hash_audit,
        "scope_limits": [
            "X-server keymap evidence only; no physical-key or application-consumption claim",
            "does not diagnose the RuntimeError cause",
            "does not establish MAP01 exit, causal benefit, or project completion",
            "posthoc read-only reconciliation; no allocation rerun or raw mutation",
        ],
        "pass": True,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pass": True, "classification": result["classification"],
                      "output": str(OUT), "owner_events": len(owner_rows),
                      "current_owner_rows_valid": all(current_row_results),
                      "non_owner_components": non_owner_components}, indent=2))


if __name__ == "__main__":
    main()
