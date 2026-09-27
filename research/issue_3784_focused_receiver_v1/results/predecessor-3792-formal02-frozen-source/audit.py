"""Independent phase-aware integrity and decision audit for Issue #3792."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys

ALLOCATION = "issue3784-explicit-x11-receiver-formal-02"
BASE = "d685f881cb5050bc42b6b96007978df9f532fe78"
IMAGE = "agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27"
FORMULA = "=B2*A2"
MATRIX = [("de-01", "de"), ("de-02", "de"), ("de-03", "de"), ("us-control", "us")]
RUNNER_SHA = "40ce0dca6bb04ab54305bbe9001c52b34600a5479dc50b8acde871009fa0751f"
MANIFEST_SHA = "b5aafca39bd927098c7074f8dbdd12e46b34c3b6f908505cbdbef54f0ebbf7e5"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def inventory(root: Path):
    return {p.relative_to(root).as_posix(): sha(p.read_bytes()) for p in sorted(root.rglob("*"))
            if p.is_file() and p.name != "raw.json"}


def expected_trace(keycodes):
    trace = []
    for chord in keycodes:
        trace.extend(("KeyPress", int(code)) for code in chord)
        trace.extend(("KeyRelease", int(code)) for code in reversed(chord))
    return trace


def phase_at_least(row, target):
    order = ["xvfb_started", "server_connected", "receiver_focused", "receiver_control",
             "baseline_captured", "layout_applied", "map_captured", "unsupported_preflight",
             "valid_preflight", "candidate_emitted", "candidate_complete"]
    try:
        return order.index(row.get("phase")) >= order.index(target)
    except ValueError:
        return False


def required_map_phases(row):
    return {name for name, target in (("baseline", "baseline_captured"), ("after", "map_captured"))
            if phase_at_least(row, target)}


def verify(raw, formal: Path, source: Path, manifest: dict, manifest_bytes: bytes,
           runner_bytes: bytes, actual_inventory: dict, source_errors=None):
    errors = list(source_errors or [])
    stops, failures, summaries = [], [], []
    if raw.get("schema") != "agent-interface/issue3784-raw-v2": errors.append("SCHEMA")
    if raw.get("allocation") != ALLOCATION: errors.append("ALLOCATION")
    if raw.get("source_base") != BASE or manifest.get("base_commit") != BASE: errors.append("BASE")
    if raw.get("candidate_blob") != manifest.get("candidate_blob") or raw.get("candidate_blob") != "9cae101a219348077668c8fc086acf8e13154afe":
        errors.append("CANDIDATE_BLOB")
    if raw.get("image") != IMAGE or raw.get("platform") != "linux/arm64" or raw.get("container_network") != "none":
        errors.append("ENVIRONMENT")
    if raw.get("xvfb_reset_mode") != "-noreset": errors.append("XVFB_RESET_MODE")
    if raw.get("runner_sha256") != RUNNER_SHA or sha(runner_bytes) != RUNNER_SHA: errors.append("RUNNER_HASH")
    if raw.get("source_manifest_sha256") != MANIFEST_SHA or sha(manifest_bytes) != MANIFEST_SHA:
        errors.append("MANIFEST_HASH")
    if raw.get("artifact_sha256") != actual_inventory: errors.append("ARTIFACT_INVENTORY")

    rows = raw.get("rows")
    if not isinstance(rows, list) or not rows:
        return errors, ["ROWS_MISSING"], failures, summaries
    ids = [r.get("case_id") for r in rows]
    expected_ids = [case_id for case_id, _ in MATRIX[:len(rows)]]
    if ids != expected_ids or len(rows) > len(MATRIX): errors.append("ROW_ORDER_OR_CARDINALITY")
    if len(rows) < len(MATRIX) and not rows[-1].get("status", "").startswith("STOP_"):
        errors.append("INCOMPLETE_WITHOUT_STOP")
    if len(rows) == len(MATRIX) and not any(r.get("status", "").startswith(("STOP_", "FAIL_"))
                                               for r in rows) and not all(
            r.get("status") == "PASS_ROW" for r in rows):
        errors.append("NONTERMINAL_ROW_STATUS")
    if any(r.get("status", "").startswith("STOP_") for r in rows[:-1]): errors.append("ROWS_AFTER_STOP")

    for index, row in enumerate(rows):
        cid, layout = MATRIX[index]
        if row.get("case_id") != cid or row.get("layout") != layout: errors.append("ROW_ID:" + cid)
        case = formal / "cases" / cid
        row_path = case / "row.json"
        if not row_path.is_file() or json.loads(row_path.read_text(encoding="utf-8")) != row:
            errors.append("ROW_BINDING:" + cid)
        if row.get("xvfb_argv", [])[-1:] != ["-noreset"]: errors.append("XVFB_NO_RESET:" + cid)
        proc = row.get("xvfb_process", {})
        if proc.get("reaped") is not True or proc.get("start_ticks") is None: errors.append("XVFB_CLEANUP:" + cid)
        phase = row.get("phase")
        status = row.get("status", "")
        if not phase: errors.append("PHASE_MISSING:" + cid)

        receiver = row.get("receiver", {})
        if phase_at_least(row, "receiver_focused"):
            if (receiver.get("class") != "InputOnly" or receiver.get("mapped") is not True
                    or receiver.get("event_mask") != 3 or row.get("focus_verified") is not True
                    or receiver.get("focus_window_id") != receiver.get("window_id")):
                stops.append("RECEIVER_FOCUS:" + cid)
        if phase_at_least(row, "receiver_control"):
            ctl = row.get("receiver_control", [])
            keycode = row.get("receiver_control_keycode")
            observed = [(e.get("type"), e.get("keycode"), e.get("lookup_text")) for e in ctl]
            want = [("KeyPress", keycode, "a"), ("KeyRelease", keycode, "a")]
            if not keycode or observed != want or row.get("receiver_control_ok") is not True:
                stops.append("RECEIVER_CONTROL:" + cid)
        elif not status.startswith("STOP_"):
            errors.append("CONTROL_PHASE_MISSING:" + cid)

        for name in required_map_phases(row):
            state = row.get(name)
            if not isinstance(state, dict):
                errors.append("MAP_STATE_MISSING:" + cid + ":" + name)
                continue
            q = state.get("query", {})
            want_layout = "us" if name == "baseline" else layout
            if q.get("returncode") != 0 or not state.get("layout_ok") or not any(
                line.strip() == f"layout: {want_layout}" for line in q.get("stdout", "").splitlines()):
                stops.append("LAYOUT_QUERY:" + cid + ":" + name)
            for suffix, value in (("xkb", state.get("dump", "").encode()),
                                  ("map.json", (json.dumps(state.get("map"), sort_keys=True) + "\n").encode())):
                path = case / f"{name}.{suffix}"
                if not path.is_file():
                    errors.append("MAP_ARTIFACT_MISSING:" + cid + ":" + name + ":" + suffix)
                elif path.read_bytes() != value:
                    errors.append("MAP_ARTIFACT_BINDING:" + cid + ":" + name + ":" + suffix)
            if sha(state.get("dump", "").encode()) != state.get("dump_sha256"):
                errors.append("DUMP_HASH:" + cid + ":" + name)
            if sha(json.dumps(state.get("map"), sort_keys=True, separators=(",", ":")).encode()) != state.get("map_sha256"):
                errors.append("MAP_HASH:" + cid + ":" + name)

        if phase_at_least(row, "map_captured"):
            gate = row.get("map_gate", {})
            changed = layout == "de"
            if (gate.get("layout_ok") is not True or gate.get("dump_changed") != changed
                    or gate.get("fresh_map_changed") != changed):
                stops.append("ACTIVE_MAP_GATE:" + cid)
            if changed and (row.get("apply", {}).get("argv") != ["setxkbmap", "-layout", "de"]
                            or row.get("apply", {}).get("returncode") != 0):
                stops.append("LAYOUT_APPLY:" + cid)
            if not changed and row.get("apply", {}).get("argv") is not None:
                errors.append("US_CONTROL_MUTATION:" + cid)

        unsupported = row.get("unsupported_preflight")
        if phase_at_least(row, "unsupported_preflight"):
            if (not unsupported or not unsupported.get("refused_zero_event")
                    or unsupported.get("events_before") or unsupported.get("events_after")
                    or unsupported.get("emissions_before") != 0 or unsupported.get("emissions_after") != 0
                    or "U+20AC" not in str(unsupported.get("error"))):
                failures.append("UNSUPPORTED_PREFLIGHT:" + cid)
        elif phase_at_least(row, "map_captured") and not status.startswith("STOP_"):
            errors.append("UNSUPPORTED_PHASE_MISSING:" + cid)

        if phase_at_least(row, "valid_preflight"):
            valid = row.get("valid_preflight", {})
            if not valid.get("zero_emission") or valid.get("events_before") or valid.get("events_after"):
                failures.append("VALID_PREFLIGHT:" + cid)

        if phase_at_least(row, "candidate_emitted"):
            events = row.get("events", [])
            plan_codes = row.get("plan_keycodes", [])
            trace = [(e.get("type"), e.get("keycode")) for e in events]
            expected = expected_trace(plan_codes)
            typed = "".join(e.get("lookup_text", "") for e in events if e.get("type") == "KeyPress")
            if trace != expected: failures.append("EVENT_TRACE:" + cid)
            if typed != FORMULA or row.get("typed") != typed: failures.append("FORMULA_TEXT:" + cid)
            if len(events) != len(expected) or row.get("emissions_after_text", 0) - row.get("emissions_before_text", 0) != len(expected):
                failures.append("EMISSION_COUNT:" + cid)
            release = row.get("release", {})
            if release.get("verified") is not True or release.get("keys_down") != [] or release.get("buttons_down") != []:
                failures.append("RELEASE_STATE:" + cid)
            if status == "PASS_ROW" and (trace != expected or typed != FORMULA):
                errors.append("FORGED_PASS:" + cid)

        if status.startswith("STOP_"):
            stops.append("ROW_STOP:" + cid + ":" + status)
        elif status.startswith("FAIL_"):
            failures.append("ROW_FAIL:" + cid + ":" + status)
        elif status == "PASS_ROW":
            pass
        else:
            errors.append("UNKNOWN_STATUS:" + cid)
        summaries.append({"case_id": cid, "phase": phase, "status": status,
                          "receiver_control_ok": row.get("receiver_control_ok"),
                          "typed": row.get("typed"), "event_count": len(row.get("events", []))})

    if any(r.get("status") == "PASS_ROW" for r in rows) and len(rows) != len(MATRIX):
        errors.append("PARTIAL_MATRIX_WITH_PASS")
    if raw.get("disposition") == "PASS_GERMAN_FORMULA_DELIVERY" and not (
            len(rows) == 4 and all(r.get("status") == "PASS_ROW" for r in rows)):
        errors.append("FORGED_PASS_DISPOSITION")
    if any(r.get("status", "").startswith("STOP_") for r in rows) and raw.get("disposition") != "STOP_GERMAN_FORMULA_DELIVERY":
        errors.append("STOP_DISPOSITION")
    if not any(r.get("status", "").startswith("STOP_") for r in rows) and any(
            r.get("status", "").startswith("FAIL_") for r in rows) and raw.get("disposition") != "FAIL_GERMAN_FORMULA_DELIVERY":
        errors.append("FAIL_DISPOSITION")
    return errors, stops, failures, summaries


def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: audit.py EVIDENCE SOURCE OUTPUT")
    formal, source, output = (Path(value).resolve() for value in sys.argv[1:])
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise SystemExit("STOP_AUDIT_OUTPUT_NOT_EMPTY")
    raw_bytes = (formal / "raw.json").read_bytes()
    raw = json.loads(raw_bytes)
    manifest_bytes = (source / "research/issue_3784_explicit_x11_receiver_v2/source_manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    runner_bytes = (source / "research/issue_3784_explicit_x11_receiver_v2/runner.py").read_bytes()
    source_errors = []
    for relative, expected in manifest.get("files", {}).items():
        data = (source / relative).read_bytes()
        if sha(data) != expected["sha256"] or blob(data) != expected["git_blob_sha1"]:
            source_errors.append("SOURCE_HASH:" + relative)
    actual = inventory(formal)
    errors, stops, failures, summaries = verify(raw, formal, source, manifest, manifest_bytes,
                                                runner_bytes, actual, source_errors)

    mutants = []
    wrong_source = copy.deepcopy(raw)
    wrong_source["candidate_blob"] = "0" * 40
    mutants.append(("wrong_candidate_source", wrong_source))
    dropped = copy.deepcopy(raw)
    dropped["rows"] = dropped.get("rows", [])[:-1]
    mutants.append(("drop_final_row", dropped))
    bad_inventory = dict(actual)
    if bad_inventory:
        first = next(iter(bad_inventory))
        bad_inventory[first] = "0" * 64
        mutants.append(("alter_artifact_hash", copy.deepcopy(raw), bad_inventory))
    if raw.get("rows"):
        wrong_control = copy.deepcopy(raw)
        wrong_control["rows"][0].setdefault("receiver_control", [{}, {}])[1]["lookup_text"] = ""
        mutants.append(("wrong_release_lookup", wrong_control))
        forged = copy.deepcopy(raw)
        forged["rows"][0]["status"] = "PASS_ROW"
        forged["rows"][0]["phase"] = "candidate_complete"
        forged["rows"][0]["typed"] = "not-the-formula"
        forged["disposition"] = "PASS_GERMAN_FORMULA_DELIVERY"
        mutants.append(("forged_candidate_pass", forged))
    challenges = []
    for entry in mutants:
        name, mutant = entry[0], entry[1]
        inv = entry[2] if len(entry) == 3 else actual
        m_errors, m_stops, m_fails, _ = verify(mutant, formal, source, manifest,
            manifest_bytes, runner_bytes, inv, source_errors)
        rejected = bool(m_errors or m_stops or m_fails)
        challenges.append({"name": name, "rejected": rejected})
        if not rejected:
            errors.append("CORRUPTION_CHALLENGE_ACCEPTED:" + name)

    phase_control = {"phase": "receiver_control", "status": "STOP_RECEIVER_CONTROL"}
    phase_aware = required_map_phases(phase_control) == set()
    challenges.append({"name": "early_stop_does_not_require_uncaptured_maps", "rejected": phase_aware})
    if not phase_aware:
        errors.append("EARLY_STOP_PHASE_GATE")

    if errors:
        disposition = "FAIL_AUDIT_INTEGRITY"
    elif stops:
        disposition = "PASS_AUDIT_CONFIRMED_STOP"
    elif failures:
        disposition = "PASS_AUDIT_CONFIRMED_FAIL"
    else:
        disposition = "PASS_AUDIT_CONFIRMED_DELIVERY"
    result = {"schema": "agent-interface/issue3784-audit-v2", "allocation": ALLOCATION,
        "disposition": disposition, "raw_disposition": raw.get("disposition"),
        "raw_sha256": sha(raw_bytes), "runner_sha256": sha(runner_bytes),
        "manifest_sha256": sha(manifest_bytes), "source_file_count": len(manifest.get("files", {})),
        "artifact_count": len(actual), "integrity_errors": errors, "setup_stops": stops,
        "semantic_failures": failures, "rows": summaries, "corruption_challenges": challenges}
    (output / "audit.json").write_text(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
