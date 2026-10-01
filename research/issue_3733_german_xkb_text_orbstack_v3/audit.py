from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath

FORMAL = Path(sys.argv[1])
OUT = Path(sys.argv[2])
HARNESS = Path("/harness")
SOURCE = Path("/src")
ALLOCATION = "issue3733-german-xkb-text-orbstack-formal-03"
IMAGE = "agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27"
FORMULA = "=B2*A2"
UNSUPPORTED = "=B2*A2€"
SCHEDULE = [("de-00", "de"), ("de-01", "de"), ("de-02", "de"), ("us-control", "us")]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_events(text: str) -> list[dict]:
    rows = []
    for block in re.split(r"(?m)(?=^(?:KeyPress|KeyRelease) event,)", text):
        kind = re.match(r"(?m)^(KeyPress|KeyRelease) event,", block)
        if not kind:
            continue
        key = re.search(r"keycode\s+(\d+)\s+\(keysym\s+0x[0-9a-fA-F]+,\s*([^)]+)\)", block)
        lookup = re.search(r"XLookupString gives \d+ bytes: \(([^)]*)\)", block)
        payload = ""
        if lookup and lookup.group(1).strip():
            try:
                payload = bytes.fromhex(lookup.group(1)).decode("ascii")
            except (ValueError, UnicodeDecodeError):
                payload = "<non-ascii>"
        rows.append({"type": kind.group(1), "keycode": int(key.group(1)) if key else None,
                     "keysym": key.group(2).strip() if key else None, "lookup_ascii": payload})
    return rows


def verify(raw: dict, actual_artifacts: dict[str, str], manifest: dict, manifest_sha: str,
           runner_sha: str, source_errors: list[str]) -> tuple[list[str], list[str]]:
    errors = list(source_errors)
    findings: list[str] = []
    if raw.get("schema") != "agent-interface/issue-3733-german-xkb-text-v3": errors.append("schema")
    if raw.get("allocation") != ALLOCATION: errors.append("allocation")
    if raw.get("source_base") != manifest.get("base_commit") or raw.get("candidate_blob") != manifest.get("candidate_blob"):
        errors.append("candidate_source_identity")
    if raw.get("candidate_sha256") != manifest.get("candidate_sha256"): errors.append("candidate_sha")
    if raw.get("source_manifest_sha256") != manifest_sha: errors.append("manifest_sha")
    if raw.get("runner_sha256") != runner_sha: errors.append("runner_sha")
    if raw.get("image_ref") != IMAGE or raw.get("platform") != "linux/arm64" or raw.get("container_network") != "none":
        errors.append("environment_identity")
    if raw.get("xvfb_reset_mode") != "-noreset": errors.append("xvfb_reset_mode")
    if actual_artifacts != raw.get("artifact_sha256"): errors.append("artifact_inventory_or_hash")

    rows = raw.get("rows")
    if not isinstance(rows, list) or not rows:
        return errors, findings + ["rows_missing"]
    if [r.get("case_id") for r in rows] != [x[0] for x in SCHEDULE[:len(rows)]]:
        findings.append("row_order_or_cardinality")
    if len(rows) > len(SCHEDULE): findings.append("too_many_rows")
    seen_xvfb: list[int] = []
    seen_xev: list[int] = []
    stop_seen = False
    semantic_fail = False

    for index, row in enumerate(rows):
        cid, expected_layout = SCHEDULE[index]
        if row.get("case_id") != cid or row.get("requested_layout") != expected_layout:
            findings.append(f"row_{index}_identity")
        if "-noreset" not in row.get("xvfb_argv", []): findings.append(f"row_{index}_xvfb_noreset")
        cleanup = row.get("xvfb_process", {})
        if cleanup:
            pid = cleanup.get("pid")
            if isinstance(pid, int): seen_xvfb.append(pid)
            if not cleanup.get("reaped") or cleanup.get("start_ticks") is None:
                findings.append(f"row_{index}_xvfb_cleanup")
        status = row.get("status", "")
        if status.startswith("STOP_"):
            stop_seen = True
            if index != len(rows) - 1: findings.append("rows_after_stop")
            if status == "STOP_GERMAN_LAYOUT_NOT_ACTIVE":
                if expected_layout != "de" or row.get("query_layout") == "de" and row.get("server_dump_changed"):
                    findings.append(f"row_{index}_false_layout_stop")
            continue

        if status.startswith("FAIL_"):
            semantic_fail = True
        elif status != "EXECUTED":
            findings.append(f"row_{index}_unexpected_status")
            continue

        if not all(row.get("extensions", {}).values()): findings.append(f"row_{index}_extensions")
        if row.get("query_layout") != expected_layout: findings.append(f"row_{index}_active_layout")
        if expected_layout == "de":
            apply = row.get("apply", {})
            if apply.get("argv") != ["setxkbmap", "-layout", "de"] or apply.get("returncode") != 0:
                findings.append(f"row_{index}_layout_apply")
            if not row.get("server_dump_changed"):
                findings.append(f"row_{index}_server_map_unchanged")

        receiver = row.get("receiver", {})
        if receiver:
            if isinstance(receiver.get("pid"), int): seen_xev.append(receiver["pid"])
            if receiver.get("start_ticks") is None: findings.append(f"row_{index}_receiver_identity")
            if not row.get("xev_process", {}).get("reaped"): findings.append(f"row_{index}_xev_cleanup")
        else:
            findings.append(f"row_{index}_receiver_missing")

        unsupported = row.get("unsupported_control", {})
        pre_path = FORMAL / "cases" / cid / "unsupported.preflight.xev.txt"
        pre_events = parse_events(pre_path.read_text(encoding="utf-8", errors="replace")) if pre_path.exists() else None
        if pre_events is None:
            findings.append(f"row_{index}_unsupported_log_missing")
        else:
            presses = sum(e["type"] == "KeyPress" for e in pre_events)
            if presses != unsupported.get("receiver_keypresses_after"):
                findings.append(f"row_{index}_unsupported_log_count")
            if presses != 0 or unsupported.get("emissions_after") != 0 or not unsupported.get("refused"):
                semantic_fail = True
                findings.append(f"row_{index}_unsupported_control")
        if row.get("candidate_plan_error") is None and "U+20AC" not in str(unsupported.get("error")):
            semantic_fail = True
            findings.append(f"row_{index}_late_unsupported_reason")

        if row.get("candidate_plan_error") is not None:
            semantic_fail = True
            if row.get("candidate_plan") is not None:
                findings.append(f"row_{index}_plan_error_has_plan")
            continue

        if status in {"FAIL_UNSUPPORTED_PREFLIGHT_EMITTED_OR_ACCEPTED", "FAIL_VALID_FORMULA_PREFLIGHT"}:
            event_path = FORMAL / "cases" / cid / "xev.log"
            if not event_path.exists():
                findings.append(f"row_{index}_xev_log_missing")
            elif any(e["type"] == "KeyPress" for e in parse_events(event_path.read_text(encoding="utf-8", errors="replace"))):
                findings.append(f"row_{index}_pre_text_input_observed")
            continue

        plan = row.get("candidate_plan")
        keycodes = row.get("candidate_plan_keycodes")
        if not isinstance(plan, list) or len(plan) != len(FORMULA) or not isinstance(keycodes, list) or len(keycodes) != len(plan):
            findings.append(f"row_{index}_plan_shape")
            semantic_fail = True
            continue
        expected_trace = []
        for chord in keycodes:
            if not isinstance(chord, list) or not chord or not all(isinstance(k, int) and k > 0 for k in chord):
                findings.append(f"row_{index}_keycodes_invalid")
                semantic_fail = True
                break
            expected_trace.extend(("KeyPress", k) for k in chord)
            expected_trace.extend(("KeyRelease", k) for k in reversed(chord))
        event_path = FORMAL / "cases" / cid / "xev.log"
        if not event_path.exists():
            findings.append(f"row_{index}_xev_log_missing")
            semantic_fail = True
            continue
        events = parse_events(event_path.read_text(encoding="utf-8", errors="replace"))
        actual_trace = [(e["type"], e["keycode"]) for e in events]
        text = "".join(e["lookup_ascii"] for e in events if e["type"] == "KeyPress")
        if actual_trace != expected_trace:
            semantic_fail = True
            findings.append(f"row_{index}_event_trace_mismatch")
        if text != FORMULA or row.get("receiver_text") != text:
            semantic_fail = True
            findings.append(f"row_{index}_receiver_text_mismatch")
        if row.get("emissions_after_text") != len(expected_trace) or len(events) != len(expected_trace):
            semantic_fail = True
            findings.append(f"row_{index}_emission_count")

    if len(seen_xvfb) != len(set(seen_xvfb)): findings.append("xvfb_pid_reuse")
    if len(seen_xev) != len(set(seen_xev)): findings.append("xev_pid_reuse")
    disposition = raw.get("disposition")
    if stop_seen and disposition != "STOP": findings.append("stop_disposition")
    if semantic_fail and disposition not in {"FAIL", "EXECUTED_PENDING_INDEPENDENT_AUDIT"}:
        findings.append("fail_disposition")
    if not stop_seen and not semantic_fail and len(rows) == len(SCHEDULE) and disposition != "EXECUTED_PENDING_INDEPENDENT_AUDIT":
        findings.append("complete_disposition")
    return errors, findings


def main() -> int:
    raw_path = FORMAL / "raw.json"
    raw_bytes = raw_path.read_bytes()
    raw = json.loads(raw_bytes)
    manifest = json.loads((HARNESS / "source_manifest.json").read_text(encoding="utf-8"))
    manifest_sha = sha((HARNESS / "source_manifest.json").read_bytes())
    runner_sha = sha((HARNESS / "run.py").read_bytes())
    source_errors = []
    for rel, expected in manifest["files"].items():
        path = SOURCE / rel
        if not path.is_file() or sha(path.read_bytes()) != expected:
            source_errors.append(f"source_file:{rel}")
    actual_artifacts = {}
    for path in sorted(FORMAL.rglob("*")):
        if path.is_symlink():
            source_errors.append(f"unsafe_symlink:{path.relative_to(FORMAL)}")
        elif path.is_file() and path.name != "raw.json":
            rel = path.relative_to(FORMAL).as_posix()
            if PurePosixPath(rel).is_absolute() or ".." in PurePosixPath(rel).parts:
                source_errors.append(f"unsafe_path:{rel}")
            actual_artifacts[rel] = sha(path.read_bytes())
    errors, findings = verify(raw, actual_artifacts, manifest, manifest_sha, runner_sha, source_errors)

    challenges = []
    mutants = []
    wrong_source = copy.deepcopy(raw); wrong_source["candidate_blob"] = "0" * 40
    mutants.append(("wrong_candidate_source", wrong_source))
    missing_row = copy.deepcopy(raw); missing_row["rows"] = missing_row.get("rows", [])[:-1]
    mutants.append(("drop_final_row", missing_row))
    if raw.get("rows"):
        executed = next((i for i, row in enumerate(raw["rows"]) if row.get("status") in {"EXECUTED", "FAIL_RECEIVER_TEXT_OR_EVENT_COUNT"}), None)
        if executed is not None:
            wrong_text = copy.deepcopy(raw)
            wrong_text["rows"][executed]["receiver_text"] = "=B2*A3"
            mutants.append(("wrong_receiver_text", wrong_text))
        else:
            forged = copy.deepcopy(raw)
            forged["rows"][0]["status"] = "EXECUTED"
            forged["rows"][0]["candidate_plan_error"] = None
            forged["rows"][0]["candidate_plan"] = []
            forged["rows"][0]["candidate_plan_keycodes"] = []
            mutants.append(("forge_execution_without_plan", forged))
        emitted = copy.deepcopy(raw)
        emitted["rows"][0].setdefault("unsupported_control", {})["emissions_after"] = 1
        mutants.append(("unsupported_preflight_emission", emitted))
    for name, mutant in mutants:
        m_errors, m_findings = verify(mutant, actual_artifacts, manifest, manifest_sha, runner_sha, source_errors)
        rejected = bool(m_errors or m_findings)
        challenges.append({"name": name, "rejected": rejected})
        if not rejected:
            errors.append(f"corruption_challenge_accepted:{name}")

    if errors:
        disposition = "FAIL_AUDIT_INTEGRITY"
    elif raw.get("disposition") == "STOP":
        disposition = "STOP_ENVIRONMENT_OR_SETUP"
    elif raw.get("disposition") == "FAIL" or findings:
        disposition = "FAIL_GERMAN_XKB_TEXT_DELIVERY"
    elif raw.get("disposition") == "EXECUTED_PENDING_INDEPENDENT_AUDIT" and len(raw.get("rows", [])) == 4 and not findings:
        disposition = "PASS_GERMAN_XKB_TEXT_DELIVERY_SCOPED"
    else:
        disposition = "HOLD_INCOMPLETE_OR_UNCLASSIFIED"
    result = {
        "allocation": ALLOCATION, "disposition": disposition,
        "formal_raw_sha256": sha(raw_bytes), "source_manifest_sha256": manifest_sha,
        "runner_sha256": runner_sha, "auditor_sha256": sha(Path(__file__).read_bytes()),
        "integrity_errors": errors, "candidate_findings": findings,
        "source_files_checked": len(manifest["files"]), "artifact_files_checked": len(actual_artifacts),
        "rows": [{"case_id": r.get("case_id"), "status": r.get("status")} for r in raw.get("rows", [])],
        "corruption_challenges": challenges,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "independent.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 1 if disposition == "FAIL_AUDIT_INTEGRITY" else 0


if __name__ == "__main__":
    raise SystemExit(main())
