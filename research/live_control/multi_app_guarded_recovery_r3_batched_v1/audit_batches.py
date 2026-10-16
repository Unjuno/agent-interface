#!/usr/bin/env python3
"""Raw-only independent audit of immutable R3 session batches."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import copy
from pathlib import Path


HERE = Path(__file__).resolve().parent
UPSTREAM = HERE / "upstream"
EXPECTED_TASK = "MULTI-APP-GUARDED-RECOVERY-R3-20260918-003"
ALLOCATION = "r3-batched-20260926-01"
EXPECTED_REFUSALS = ["REFUSE_GEOMETRY", "REFUSE_FOCUS", "REFUSE_BINDING", "REFUSE_OBSERVATION"] * 3
EXPECTED_TITLES = [
    "chrome://downloads/ - Chromium",
    "chrome://history/ - Chromium",
    "chrome://downloads/ - Chromium",
    "chrome://history/ - Chromium",
] * 3


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def audit_row(row: dict[str, object], batch: dict[str, object], expected_id: int, source_files: dict[str, str], image: dict[str, str]) -> list[str]:
    problems: list[str] = []
    if batch.get("session_id") != expected_id or row.get("session_id") != expected_id:
        problems.append("session_identity")
    if row.get("task") != EXPECTED_TASK or batch.get("task") != EXPECTED_TASK:
        problems.append("task_identity")
    if batch.get("source_files") != source_files or batch.get("image") != image:
        problems.append("batch_provenance")
    if row.get("cycles_completed") != 3:
        problems.append("cycles_completed")
    refusals = row.get("refusals", [])
    if [v.get("reason") for v in refusals] != EXPECTED_REFUSALS:
        problems.append("refusal_sequence")
    if [v.get("cycle") for v in refusals] != [c for c in range(1, 4) for _ in range(4)]:
        problems.append("refusal_cycle_order")
    if any(v.get("input_before") != v.get("input_after") for v in refusals):
        problems.append("stale_refusal_emitted_input")
    actions = row.get("task_batches", [])
    if len(actions) != 12 or row.get("task_input_batches") != 12:
        problems.append("action_batch_count")
    if any(v.get("active_before") != v.get("window") for v in actions):
        problems.append("wrong_active_target")
    if any(v.get("input_after") != v.get("input_before", 0) + 1 for v in actions):
        problems.append("action_ledger_sequence")
    events = batch.get("input_event_receipts", [])
    if not events or any(v.get("status") != "REQUEST_SENT" for v in events):
        problems.append("input_event_receipts")
    if sum(v.get("event") == "KeyPress" for v in events) != sum(v.get("event") == "KeyRelease" for v in events):
        problems.append("unbalanced_key_edges")
    if [v.get("title") for v in row.get("effects", [])] != EXPECTED_TITLES:
        problems.append("effect_sequence")
    if [v.get("cycle") for v in row.get("effects", [])] != [c for c in range(1, 4) for _ in range(4)]:
        problems.append("effect_cycle_order")
    replacements = row.get("replacements", [])
    if len(replacements) != 3:
        problems.append("replacement_count")
    if any(v.get("old_window") == v.get("new_window") or v.get("old_gone") is not True for v in replacements):
        problems.append("replacement_lineage")
    process_receipts = batch.get("process_receipts", [])
    if len(process_receipts) < 7 or any(v.get("returncode_after_stop") is None or v.get("error") for v in process_receipts):
        problems.append("process_cleanup_receipts")
    if batch.get("cleanup_residues") or batch.get("x11_socket_present_after_cleanup") is not False:
        problems.append("process_cleanup_residue")
    if row.get("terminal_neutral") is not True:
        problems.append("terminal_input_not_neutral")
    if sorted(row.get("apps", [])) != ["Chromium", "XTerm"]:
        problems.append("application_set")
    if row.get("errors") != batch.get("candidate_errors", []) + batch.get("cleanup_errors", []):
        problems.append("row_error_reconciliation")
    if row.get("pass") is not (not row.get("errors")):
        problems.append("row_pass_reconciliation")
    return sorted(set(problems))


def recompute(rows: list[dict[str, object]], source_files: dict[str, str], image: dict[str, str]) -> dict[str, object]:
    session_rows = [b["row"] for b in rows]
    all_errors: list[str] = []
    for batch in rows:
        all_errors.extend(f"session{batch['session_id']}:{e}" for e in batch["audit_errors"])
        all_errors.extend(f"session{batch['session_id']}:{e}" for e in batch["candidate_errors"])
        all_errors.extend(f"session{batch['session_id']}:{e}" for e in batch["cleanup_errors"])
    result: dict[str, object] = {
        "task": EXPECTED_TASK,
        "formal_invocations": 1,
        "reruns": 0,
        "replacements_budget": 0,
        "tuning": 0,
        "sessions": len(rows),
        "cycles_per_session": 3,
        "passed_sessions": sum(r.get("pass") is True for r in session_rows),
        "errors": all_errors,
        "aggregate": {
            "refusals": sum(len(r.get("refusals", [])) for r in session_rows),
            "refusal_zero_task_input": sum(sum(v.get("input_before") == v.get("input_after") for v in r.get("refusals", [])) for r in session_rows),
            "fallback_batches": sum(len(r.get("task_batches", [])) for r in session_rows),
            "fallback_active_match": sum(sum(v.get("active_before") == v.get("window") for v in r.get("task_batches", [])) for r in session_rows),
            "effects": sum(len(r.get("effects", [])) for r in session_rows),
            "replacement_valid": sum(sum(v.get("old_window") != v.get("new_window") and v.get("old_gone") is True for v in r.get("replacements", [])) for r in session_rows),
            "terminal_neutral": sum(r.get("terminal_neutral") is True for r in session_rows),
        },
        "descriptive": {
            "sessions_with_nonconsecutive_raw_xid_reuse": sum(
                len({v.get("old_window") for v in r.get("replacements", [])} | {v.get("new_window") for v in r.get("replacements", [])}) < 4
                for r in session_rows
            )
        },
        "environment": {
            "python": image["python"],
            "platform": image["runtime_platform"],
            "chromium": image["chromium"],
            "xterm": image["xterm"],
            "x11": "private Xvfb/Openbox",
        },
        "provenance": {"source_files": source_files, "image": image},
        "decision": "PASS_MULTI_APP_GUARDED_RECOVERY_R3_SCOPED" if len(rows) == 4 and not all_errors else "FAIL_MULTI_APP_GUARDED_RECOVERY_R3",
        "rows": session_rows,
    }
    result["summary_digest_sha256"] = digest(json.dumps({k: v for k, v in result.items() if k != "rows"}, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode())
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    evidence = args.evidence.resolve()
    out = args.out.resolve()
    if not out.is_dir() or any(out.iterdir()):
        raise SystemExit("STOP_AUDIT_OUTPUT_NOT_FRESH")
    manifest_path = evidence / "BATCH_MANIFEST.json"
    if not manifest_path.is_file():
        result = {"decision": "HOLD_FORMAL_ALLOCATION_INCOMPLETE", "reason": "batch manifest missing", "errors": []}
        (out / "INDEPENDENT_AUDIT.json").write_bytes(canonical(result))
        print(json.dumps(result, sort_keys=True))
        return 2
    manifest_raw = manifest_path.read_bytes()
    manifest = json.loads(manifest_raw)
    failures: list[str] = []
    source_meta = json.loads((UPSTREAM / "SOURCE_MANIFEST.json").read_text()) if (UPSTREAM / "SOURCE_MANIFEST.json").exists() else None
    if manifest.get("task") != EXPECTED_TASK or manifest.get("formal_allocation") != ALLOCATION:
        failures.append("manifest_identity")
    if source_meta and manifest.get("source_bundle_sha256") != source_meta["SOURCE_BUNDLE.tar.gz"]["sha256"]:
        failures.append("source_bundle_identity")
    batch_rows: list[dict[str, object]] = []
    records = manifest.get("batches", [])
    expected_by_id = {r.get("session_id"): r for r in records}
    if len(expected_by_id) != len(records):
        failures.append("duplicate_manifest_batch")
    for session_id in range(1, 5):
        record = expected_by_id.get(session_id)
        path = evidence / f"session_{session_id:02d}.json"
        if record is None or not path.is_file():
            continue
        raw = path.read_bytes()
        if record.get("path") != path.name or record.get("bytes") != len(raw) or record.get("sha256") != digest(raw):
            failures.append(f"batch_hash:{session_id}")
            continue
        batch = json.loads(raw)
        if batch.get("allocation") != ALLOCATION or batch.get("session_id") != session_id:
            failures.append(f"batch_identity:{session_id}")
        if batch.get("source_files") != manifest.get("source_files") or batch.get("image") != manifest.get("image"):
            failures.append(f"batch_provenance:{session_id}")
        for log in batch.get("session_root_logs", []):
            try:
                data = base64.b64decode(log["raw_base64"], validate=True)
            except Exception:
                failures.append(f"log_encoding:{session_id}")
                continue
            if len(data) != log.get("bytes") or digest(data) != log.get("sha256"):
                failures.append(f"log_hash:{session_id}:{log.get('path')}")
        batch["audit_errors"] = audit_row(batch.get("row", {}), batch, session_id, manifest.get("source_files", {}), manifest.get("image", {}))
        if batch["audit_errors"]:
            failures.extend(f"session{session_id}:{e}" for e in batch["audit_errors"])
        if batch.get("row", {}).get("errors") != batch.get("candidate_errors", []) + batch.get("cleanup_errors", []):
            failures.append(f"candidate_error_reconciliation:{session_id}")
        batch_rows.append(batch)

    if len(batch_rows) < 4:
        status = "HOLD_FORMAL_ALLOCATION_INCOMPLETE" if not failures else "FAIL_RECOVERY_OR_INTEGRITY"
        audit = {"decision": status, "complete_sessions": [b.get("session_id") for b in batch_rows], "errors": failures, "batch_manifest_sha256": digest(manifest_raw)}
        (out / "INDEPENDENT_AUDIT.json").write_bytes(canonical(audit))
        print(json.dumps(audit, sort_keys=True))
        return 2

    controls: dict[str, bool] = {}
    sample = batch_rows[0]
    mutations = {
        "missing_refusal": lambda b: b["row"]["refusals"].pop(),
        "stale_refusal_input": lambda b: b["row"]["refusals"][0].__setitem__("input_after", 99),
        "wrong_active_window": lambda b: b["row"]["task_batches"][0].__setitem__("active_before", 0),
        "wrong_effect_title": lambda b: b["row"]["effects"][0].__setitem__("title", "wrong"),
        "replacement_not_retired": lambda b: b["row"]["replacements"][0].__setitem__("old_gone", False),
        "non_neutral_terminal": lambda b: b["row"].__setitem__("terminal_neutral", False),
        "release_edge_missing": lambda b: b["input_event_receipts"].pop(),
        "process_exit_missing": lambda b: b["process_receipts"][0].__setitem__("returncode_after_stop", None),
        "wrong_source_identity": lambda b: b["source_files"].__setitem__("common.py", "0" * 64),
        "wrong_image_identity": lambda b: b["image"].__setitem__("image_id", "sha256:" + "0" * 64),
    }
    for name, mutate in mutations.items():
        damaged = copy.deepcopy(sample)
        mutate(damaged)
        controls[name] = bool(audit_row(damaged["row"], damaged, 1, manifest["source_files"], manifest["image"]))
    if not all(controls.values()):
        failures.append("corruption_controls")
    result = recompute(batch_rows, manifest["source_files"], manifest["image"])
    stored = json.loads((evidence / "RESULT.json").read_bytes())
    reconstructed_raw = (json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()
    stored_raw = (json.dumps(stored, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()
    if reconstructed_raw != stored_raw:
        failures.append("aggregate_reconstruction_mismatch")
    if result["decision"] != "PASS_MULTI_APP_GUARDED_RECOVERY_R3_SCOPED":
        failures.append("r3_gates_not_passed")
    result_no_audit = dict(result)
    for key in ("rows", "summary_digest_sha256"):
        result_no_audit.pop(key, None)
    audit = {
        "decision": "PASS_R3_BATCHES_INDEPENDENTLY_RECONSTRUCTED" if not failures else "FAIL_RECOVERY_OR_INTEGRITY",
        "errors": failures,
        "complete_sessions": [b["session_id"] for b in batch_rows],
        "batch_count": len(batch_rows),
        "batch_manifest_sha256": digest(manifest_raw),
        "reconstructed_result_sha256": digest(reconstructed_raw),
        "result_summary": result_no_audit,
        "mutation_controls": controls,
    }
    (out / "RECONSTRUCTED_RESULT.json").write_bytes(reconstructed_raw)
    (out / "INDEPENDENT_AUDIT.json").write_bytes(canonical(audit))
    print(json.dumps({"decision": audit["decision"], "errors": failures, "batch_count": len(batch_rows), "reconstructed_result_sha256": audit["reconstructed_result_sha256"]}, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
