"""Independent raw-only audit for the #3240 two-session diagnostic."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

TEXT = "gtk3240"
REPO_ROOT = Path(__file__).resolve().parents[3]


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_pid(identity):
    match = re.search(r"_NET_WM_PID\(CARDINAL\) = (\d+)", identity["xprop"])
    return int(match.group(1)) if match else None


def parse_geom(identity):
    text = identity["xwininfo"]
    fields = {}
    for name in ("Width", "Height", "Absolute upper-left X", "Absolute upper-left Y"):
        match = re.search(r"^\s*" + re.escape(name) + r":\s*(-?\d+)", text, re.MULTILINE)
        fields[name] = int(match.group(1)) if match else None
    return fields


def valid_identity(identity):
    return (identity["xid"] > 0 and parse_pid(identity) is not None and
            '"AgentInterfaceGtkFixture"' in identity["xprop"] and
            parse_geom(identity) == {
                "Width": 400, "Height": 180,
                "Absolute upper-left X": 0, "Absolute upper-left Y": 0,
            })


def audit_case(root, dirname, decoy):
    case = root / dirname
    errors = []
    pre = read_json(case / "target_identity_pre.json")
    post = read_json(case / "target_identity_post.json")
    row = read_json(case / "row.json")
    processes = read_json(case / "processes.json")
    if not valid_identity(pre) or not valid_identity(post):
        errors.append("target_identity_invalid")
    if pre != post or row.get("target_identity_same") is not True:
        errors.append("target_identity_changed")
    if int(row.get("target_window_id", -1)) != pre["xid"]:
        errors.append("row_target_xid_mismatch")
    if parse_pid(pre) != row.get("target_pid"):
        errors.append("target_pid_mismatch")
    measured_pre = case / ("target_pre.xwd" if decoy else "target_ready_pre_action.xwd")
    if row.get("target_initial_sha256") != digest(case / "target_pre.xwd"):
        errors.append("target_initial_hash_mismatch")
    if row.get("target_pre_sha256") != digest(measured_pre):
        errors.append("target_pre_hash_mismatch")
    if row.get("target_post_sha256") != digest(case / "target_post.xwd"):
        errors.append("target_post_hash_mismatch")
    if any(p.get("returncode") is None for p in processes):
        errors.append("process_not_reaped")
    if decoy:
        di = read_json(case / "decoy_identity.json")
        if not valid_identity(di):
            errors.append("decoy_identity_invalid")
        if di["xid"] == pre["xid"] or parse_pid(di) == parse_pid(pre):
            errors.append("decoy_identity_not_distinct")
        if parse_geom(di) != parse_geom(pre):
            errors.append("decoy_geometry_mismatch")
        if '"AgentInterfaceGtkFixture"' not in di["xprop"]:
            errors.append("decoy_title_mismatch")
        if row.get("decoy_sha256") != digest(case / "decoy_saved_looking.xwd"):
            errors.append("decoy_hash_mismatch")
        if row.get("decoy_sha256") == row.get("target_initial_sha256"):
            errors.append("decoy_pixels_not_changed")
        if row.get("target_pre_sha256") != row.get("target_post_sha256"):
            errors.append("untouched_target_pixels_changed")
        if (case / "effect.json").exists():
            errors.append("decoy_effect_file_exists")
        events = (case / "app-events.jsonl").read_text(encoding="utf-8").splitlines() if (case / "app-events.jsonl").exists() else []
        if events:
            errors.append("target_app_received_events")
        if row.get("visual_only_would_accept") is not True:
            errors.append("visual_only_negative_control_not_exercised")
        disposition = "REJECT_DECOY"
    else:
        effect = read_json(case / "effect.json") if (case / "effect.json").exists() else None
        if effect != {"saved": True, "text": TEXT}:
            errors.append("exact_app_effect_missing")
        events = [json.loads(line) for line in (case / "app-events.jsonl").read_text(encoding="utf-8").splitlines() if line]
        if not any(event.get("type") == "save" for event in events):
            errors.append("app_save_event_missing")
        if row.get("target_pre_sha256") == row.get("target_post_sha256"):
            errors.append("target_pixels_unchanged")
        results = [read_json(case / name) for name in ("adapter-prep.json", "adapter-action.json")]
        for result in results:
            if result.get("program_completed") is not True:
                errors.append("adapter_program_not_completed")
            if result.get("task_success") is not None:
                errors.append("adapter_claimed_unscored_task_success")
            raw = result.get("raw_dispatch", {})
            execution = raw.get("result", {}).get("execution", {})
            if raw.get("status") != "returned" or execution.get("status") != "completed":
                errors.append("native_execution_not_completed")
            releases = execution.get("releases")
            if not isinstance(releases, list) or not releases:
                errors.append("release_receipt_missing")
            elif any(item.get("keys_down") or item.get("buttons_down") or
                     item.get("verified") is not True
                     for item in releases if isinstance(item, dict)):
                errors.append("release_not_empty")
        disposition = "ACCEPT_APPLICATION_EFFECT"
    return {"case": row.get("case"), "decision": disposition,
            "errors": errors, "target_xid": pre["xid"],
            "target_pid": parse_pid(pre), "target_pre_sha256": digest(measured_pre),
            "target_post_sha256": digest(case / "target_post.xwd"),
            "processes": processes}


def audit_freeze(root):
    freeze_path = root / "freeze.json"
    if not freeze_path.exists():
        return ["freeze_missing"], {}
    freeze = read_json(freeze_path)
    errors = []
    if freeze.get("schema") != "issue3240_gtk_effect_control_freeze_v1":
        errors.append("freeze_schema")
    checked = {}
    for relpath, expected in freeze.get("source_sha256", {}).items():
        path = REPO_ROOT / relpath
        if not path.is_file():
            checked[relpath] = {"present": False}
            errors.append("freeze_source_missing:" + relpath)
            continue
        actual = digest(path).upper()
        checked[relpath] = {"present": True, "expected": expected, "actual": actual,
                            "match": actual == expected.upper()}
        if actual != expected.upper():
            errors.append("freeze_source_hash:" + relpath)
    return errors, checked


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("evidence", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    root = args.evidence.resolve()
    rows = [audit_case(root, "01_application_save", False),
            audit_case(root, "02_render_only_decoy", True)]
    errors = [f"{row['case']}:{item}" for row in rows for item in row["errors"]]
    freeze_errors, frozen_sources = audit_freeze(root)
    errors.extend(freeze_errors)
    runner_summary_path = root / "runner-summary.json"
    if not runner_summary_path.exists():
        errors.append("runner_summary_missing")
        runner_summary = None
    else:
        runner_summary = read_json(runner_summary_path)
        if runner_summary.get("decision") != "RUN_COMPLETED_PENDING_INDEPENDENT_AUDIT":
            errors.append("runner_summary_disposition")
    decision = "PASS_APP_EFFECT_DISCRIMINATED" if not errors else "HOLD_EVIDENCE_OR_EFFECT_BOUNDARY"
    artifacts = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            artifacts[str(path.relative_to(root))] = {"sha256": digest(path), "bytes": path.stat().st_size}
    result = {"decision": decision, "scope": "two-row live GTK app-effect vs render-only decoy diagnostic",
              "sessions": len(rows), "expected_sessions": 2, "errors": errors,
              "rows": rows, "frozen_source_audit": frozen_sources,
              "runner_summary": runner_summary, "artifact_manifest": artifacts,
              "formal_2606_acceptance": False, "model_calls": 0, "provider_calls": 0}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
