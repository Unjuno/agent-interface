from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath


ALLOCATION = "issue3733-german-xkb-text-orbstack-formal-01"
FORMULA = "=B2*A2"
UNSUPPORTED = "=B2*A2€"
EXPECTED_IMAGE = "agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27"
EXPECTED_SOURCE_BASE = "eca4bcc1ee839b80442397e27f238c97d6dd6bb4"
EXPECTED_CANDIDATE_BLOB = "9cae101a219348077668c8fc086acf8e13154afe"
EXPECTED_LAYOUTS = [("de-00", "de"), ("de-01", "de"), ("de-02", "de"), ("us-control", "us")]
HARNESS = Path("/harness")
SOURCE_ROOT = Path("/src")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return sha256(path.read_bytes())


def parse_xev_events(text: str) -> list[dict]:
    """Independent parse of xev's XLookupString output, not runner JSON."""
    events = []
    blocks = re.split(r"(?m)(?=^(?:KeyPress|KeyRelease) event,)", text)
    for block in blocks:
        first = re.match(r"(?m)^(KeyPress|KeyRelease) event,", block)
        if not first:
            continue
        code = re.search(r"keycode\s+(\d+)\s+\(keysym\s+0x[0-9a-fA-F]+,\s*([^)]+)\)", block)
        state = re.search(r"(?m)^\s*state\s+0x([0-9a-fA-F]+)", block)
        lookup = re.search(r"XLookupString gives \d+ bytes: \(([^)]*)\)", block)
        raw_bytes = b""
        if lookup and lookup.group(1).strip():
            try:
                raw_bytes = bytes.fromhex(lookup.group(1))
            except ValueError:
                raw_bytes = b"\xff"
        events.append({
            "type": first.group(1),
            "keycode": int(code.group(1)) if code else None,
            "keysym": code.group(2).strip() if code else None,
            "state": int(state.group(1), 16) if state else None,
            "lookup_hex": raw_bytes.hex(),
            "lookup_ascii": raw_bytes.decode("ascii", "replace"),
        })
    return events


def reconstructed_plan(row: dict) -> list[list[str]] | None:
    levels = row.get("active_symbol_levels")
    if not isinstance(levels, dict):
        return None
    plan = []
    for char in FORMULA:
        if char in "=*":
            entry = levels.get(char)
            if not isinstance(entry, dict):
                return None
            if entry.get("level0") == ord(char):
                plan.append([entry.get("keysym_name")])
            elif entry.get("level1") == ord(char):
                plan.append(["SHIFT", entry.get("keysym_name")])
            else:
                return None
        elif char.isupper():
            plan.append(["SHIFT", char.lower()])
        else:
            plan.append([char])
    return plan


def semantic_findings(raw: dict) -> list[str]:
    findings = []
    if raw.get("schema") != "agent-interface/issue-3733-german-xkb-text-v1":
        findings.append("raw_schema")
    if raw.get("allocation") != ALLOCATION:
        findings.append("allocation_identity")
    if raw.get("source_base") != EXPECTED_SOURCE_BASE or raw.get("candidate_blob") != EXPECTED_CANDIDATE_BLOB:
        findings.append("source_identity")
    if raw.get("image_ref") != EXPECTED_IMAGE or raw.get("platform") != "linux/arm64" or raw.get("container_network") != "none":
        findings.append("environment_identity")
    rows = raw.get("rows")
    if not isinstance(rows, list) or not rows:
        return findings + ["rows_missing"]
    actual_ids = [row.get("case_id") for row in rows if isinstance(row, dict)]
    expected_prefix = [item[0] for item in EXPECTED_LAYOUTS[:len(actual_ids)]]
    if actual_ids != expected_prefix:
        findings.append("case_order_or_cardinality")
    if len(rows) > len(EXPECTED_LAYOUTS):
        findings.append("too_many_rows")

    stop_seen = False
    any_candidate_fail = False
    server_pids = []
    receiver_pids = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            findings.append(f"row_{index}_not_object")
            continue
        expected_id, expected_layout = EXPECTED_LAYOUTS[index]
        if row.get("case_id") != expected_id or row.get("requested_layout") != expected_layout:
            findings.append(f"row_{index}_identity")
        status = row.get("status", "")
        server = row.get("xvfb_process", {})
        if server:
            server_pids.append(server.get("pid"))
            if not server.get("reaped") or server.get("start_ticks") is None:
                findings.append(f"row_{index}_xvfb_not_reaped")
        if status.startswith("STOP_"):
            stop_seen = True
            if index != len(rows) - 1:
                findings.append("rows_after_stop")
            if status == "STOP_SETUP_BLOCKED_NATIVE_XKB_APPLY":
                apply = row.get("apply", {})
                after = row.get("after", {})
                if apply.get("argv") != ["setxkbmap", "-layout", "de"] or apply.get("returncode") != 0:
                    findings.append("stop_apply_identity")
                if after.get("layout") == "de" and after.get("server_changed") and after.get("core_map_changed"):
                    findings.append("false_setup_stop")
            continue
        if status.startswith("FAIL_"):
            any_candidate_fail = True
            findings.append(f"candidate_row_failure:{status}")
            continue
        if status != "EXECUTED":
            findings.append(f"row_{index}_unexpected_status")
            continue

        receiver = row.get("xev_process", {})
        receiver_pids.append(receiver.get("pid"))
        if not receiver.get("reaped") or receiver.get("start_ticks") is None:
            findings.append(f"row_{index}_xev_not_reaped")

        after = row.get("after", {})
        if after.get("layout") != expected_layout:
            findings.append(f"row_{index}_active_layout")
        if expected_layout == "de":
            apply = row.get("apply", {})
            if apply.get("argv") != ["setxkbmap", "-layout", "de"] or apply.get("returncode") != 0:
                findings.append(f"row_{index}_apply")
            if not after.get("server_changed") or not after.get("core_map_changed"):
                findings.append(f"row_{index}_map_transition")

        expected_plan = reconstructed_plan(row)
        if expected_plan is None:
            findings.append(f"row_{index}_symbol_not_representable")
            any_candidate_fail = True
        elif row.get("candidate_plan") != expected_plan:
            findings.append(f"row_{index}_plan_disagrees_with_map")
            any_candidate_fail = True

        keycodes = row.get("candidate_plan_keycodes")
        if not isinstance(keycodes, list) or len(keycodes) != len(FORMULA):
            findings.append(f"row_{index}_plan_keycodes_shape")
            any_candidate_fail = True
        else:
            expected_trace = []
            for chord in keycodes:
                if not isinstance(chord, list) or not chord or not all(isinstance(code, int) and code > 0 for code in chord):
                    findings.append(f"row_{index}_invalid_chord_keycodes")
                    any_candidate_fail = True
                    break
                expected_trace.extend(("KeyPress", code) for code in chord)
                expected_trace.extend(("KeyRelease", code) for code in reversed(chord))
            log_path = Path("/formal") / "cases" / expected_id / "xev.log"
            if log_path.exists():
                parsed = parse_xev_events(log_path.read_text(encoding="utf-8", errors="replace"))
                observed_trace = [(event["type"], event["keycode"]) for event in parsed]
                if observed_trace != expected_trace:
                    findings.append(f"row_{index}_event_trace_mismatch")
                    any_candidate_fail = True
                actual_text = "".join(event["lookup_ascii"] for event in parsed if event["type"] == "KeyPress")
                if actual_text != FORMULA or row.get("receiver_text") != actual_text:
                    findings.append(f"row_{index}_receiver_text_mismatch")
                    any_candidate_fail = True
                if row.get("emissions_after_text") != len(expected_trace) or len(parsed) != len(expected_trace):
                    findings.append(f"row_{index}_emission_count_mismatch")
                    any_candidate_fail = True
            else:
                findings.append(f"row_{index}_xev_log_missing")
                any_candidate_fail = True

        control = row.get("unsupported_control", {})
        if not control.get("refused") or "U+20AC" not in str(control.get("error")):
            findings.append(f"row_{index}_late_unsupported_not_refused")
            any_candidate_fail = True
        if control.get("emissions_after") != 0 or control.get("receiver_keypresses_after") != 0:
            findings.append(f"row_{index}_unsupported_preflight_emitted")
            any_candidate_fail = True
        preflight_path = Path("/formal") / "cases" / expected_id / "unsupported.preflight.xev.txt"
        if preflight_path.exists():
            preflight_events = parse_xev_events(preflight_path.read_text(encoding="utf-8", errors="replace"))
            preflight_presses = sum(event["type"] == "KeyPress" for event in preflight_events)
            if preflight_presses != 0 or preflight_presses != control.get("receiver_keypresses_after"):
                findings.append(f"row_{index}_unsupported_preflight_log_mismatch")
                any_candidate_fail = True
        else:
            findings.append(f"row_{index}_unsupported_preflight_log_missing")

    if len(server_pids) != len(set(server_pids)):
        findings.append("xvfb_pid_reused")
    if len(receiver_pids) != len(set(receiver_pids)):
        findings.append("xev_pid_reused")

    disposition = raw.get("disposition")
    if disposition != "STOP" and len(rows) != len(EXPECTED_LAYOUTS):
        findings.append("incomplete_nonstop_schedule")
    if stop_seen and disposition != "STOP":
        findings.append("stop_disposition_mismatch")
    if any_candidate_fail and disposition not in {"FAIL", "EXECUTED_PENDING_INDEPENDENT_AUDIT"}:
        findings.append("failure_disposition_mismatch")
    if not stop_seen and not any_candidate_fail and disposition not in {"FAIL", "EXECUTED_PENDING_INDEPENDENT_AUDIT"}:
        findings.append("complete_disposition_mismatch")
    return findings


def run_audit(raw_path: Path, formal_root: Path, audit_out: Path) -> dict:
    errors = []
    raw_bytes = raw_path.read_bytes()
    raw = json.loads(raw_bytes)
    expected_manifest = json.loads((HARNESS / "source_manifest.json").read_text(encoding="utf-8"))
    manifest_sha = file_sha(HARNESS / "source_manifest.json")
    runner_sha = file_sha(HARNESS / "run.py")
    auditor_sha = file_sha(HARNESS / "audit.py")
    if raw.get("source_manifest_sha256") != manifest_sha:
        errors.append("source_manifest_hash")
    if raw.get("runner_sha256") != runner_sha:
        errors.append("runner_hash")
    if expected_manifest.get("base_commit") != EXPECTED_SOURCE_BASE or expected_manifest.get("candidate_blob") != EXPECTED_CANDIDATE_BLOB:
        errors.append("frozen_manifest_identity")
    for relpath, expected in expected_manifest["files"].items():
        path = SOURCE_ROOT / relpath
        if not path.is_file() or file_sha(path) != expected:
            errors.append(f"source_file:{relpath}")

    expected_artifacts = raw.get("artifact_sha256")
    actual_artifacts = {}
    for path in sorted(formal_root.rglob("*")):
        if path.is_symlink():
            errors.append(f"unsafe_symlink:{path.relative_to(formal_root)}")
        elif path.is_file() and path.name != "raw.json":
            rel = path.relative_to(formal_root).as_posix()
            p = PurePosixPath(rel)
            if p.is_absolute() or ".." in p.parts:
                errors.append(f"unsafe_path:{rel}")
            actual_artifacts[rel] = file_sha(path)
    if actual_artifacts != expected_artifacts:
        errors.append("artifact_inventory_or_hash")
    if raw.get("image_ref") != EXPECTED_IMAGE or raw.get("platform") != "linux/arm64" or raw.get("container_network") != "none":
        errors.append("runtime_identity")
    if raw.get("allocation") != ALLOCATION:
        errors.append("allocation_identity")

    findings = semantic_findings(raw)
    challenges = []
    mutations = []
    missing = copy.deepcopy(raw)
    missing["rows"] = missing.get("rows", [])[:-1]
    mutations.append(("drop_last_row", missing))
    reordered = copy.deepcopy(raw)
    if len(reordered.get("rows", [])) > 1:
        reordered["rows"][0], reordered["rows"][1] = reordered["rows"][1], reordered["rows"][0]
    else:
        reordered.setdefault("rows", []).append(copy.deepcopy(reordered["rows"][0]))
    mutations.append(("reorder_or_duplicate_rows", reordered))
    wrong_source = copy.deepcopy(raw)
    wrong_source["candidate_blob"] = "0" * 40
    mutations.append(("replace_candidate_source", wrong_source))
    if raw.get("rows"):
        if any(row.get("status") == "EXECUTED" for row in raw["rows"]):
            emitted = copy.deepcopy(raw)
            target = next(row for row in emitted["rows"] if row.get("status") == "EXECUTED")
            target.setdefault("unsupported_control", {})["emissions_after"] = 2
            mutations.append(("unsupported_control_emission", emitted))
            wrong_text = copy.deepcopy(raw)
            target = next(row for row in wrong_text["rows"] if row.get("status") == "EXECUTED")
            target["receiver_text"] = "=B2*A3"
            mutations.append(("wrong_receiver_text", wrong_text))
        else:
            forged = copy.deepcopy(raw)
            forged["rows"][0]["status"] = "EXECUTED"
            mutations.append(("forge_execution_without_trace", forged))
    for name, mutant in mutations:
        rejected = bool(semantic_findings(mutant))
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
        "schema": "agent-interface/issue-3733-independent-audit-v1",
        "allocation": ALLOCATION,
        "disposition": disposition,
        "formal_raw_sha256": sha256(raw_bytes),
        "source_manifest_sha256": manifest_sha,
        "runner_sha256": runner_sha,
        "auditor_sha256": auditor_sha,
        "integrity_errors": errors,
        "candidate_findings": findings,
        "source_files_checked": len(expected_manifest["files"]),
        "artifact_files_checked": len(actual_artifacts),
        "rows": [{"case_id": row.get("case_id"), "status": row.get("status")} for row in raw.get("rows", [])],
        "corruption_challenges": challenges,
        "corruption_rejections": sum(challenge["rejected"] for challenge in challenges),
    }
    if audit_out.exists() and any(audit_out.iterdir()):
        raise RuntimeError("AUDIT_OUTPUT_DIRECTORY_NOT_EMPTY")
    audit_out.mkdir(parents=True, exist_ok=True)
    (audit_out / "independent.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def self_test() -> int:
    sample = {
        "schema": "agent-interface/issue-3733-german-xkb-text-v1",
        "allocation": ALLOCATION,
        "source_base": EXPECTED_SOURCE_BASE,
        "candidate_blob": EXPECTED_CANDIDATE_BLOB,
        "image_ref": EXPECTED_IMAGE,
        "platform": "linux/arm64",
        "container_network": "none",
        "disposition": "STOP",
        "rows": [{
            "case_id": "de-00",
            "requested_layout": "de",
            "status": "STOP_SETUP_BLOCKED_NATIVE_XKB_APPLY",
            "xvfb_process": {"pid": 41, "start_ticks": "10", "reaped": True},
            "apply": {"argv": ["setxkbmap", "-layout", "de"], "returncode": 0},
            "after": {"layout": "us", "server_changed": False, "core_map_changed": False},
        }],
    }
    if semantic_findings(sample):
        print("SELF_TEST_FAIL_VALID_STOP_REJECTED")
        return 1
    mutations = []
    missing = copy.deepcopy(sample)
    missing["rows"] = []
    mutations.append(missing)
    wrong_source = copy.deepcopy(sample)
    wrong_source["candidate_blob"] = "0" * 40
    mutations.append(wrong_source)
    forged = copy.deepcopy(sample)
    forged["rows"][0]["status"] = "EXECUTED"
    mutations.append(forged)
    if not all(semantic_findings(mutant) for mutant in mutations):
        print("SELF_TEST_FAIL_MUTATION_ACCEPTED")
        return 1
    print("SELF_TEST_PASS valid_stop=1 corruptions_rejected=3")
    return 0


def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        return self_test()
    if len(sys.argv) != 3:
        print("usage: audit.py FORMAL_ROOT AUDIT_OUT", file=sys.stderr)
        return 64
    formal_root = Path(sys.argv[1])
    result = run_audit(formal_root / "raw.json", formal_root, Path(sys.argv[2]))
    print(json.dumps(result, sort_keys=True))
    return 1 if result["disposition"] == "FAIL_AUDIT_INTEGRITY" else 0


if __name__ == "__main__":
    raise SystemExit(main())
