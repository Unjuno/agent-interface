"""Independent read-only audit of a retained Issue #3784 formal allocation."""
import hashlib
import json
from pathlib import Path
import sys

BASE = "f319d64a0de28ba765f86772123308e3d96baac2"
IMAGE = "agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27"
RUNNER_SHA = "08e9292718e53534ab0b9f483e09fffab57bb1357d36dbe5b4b6fd40aa36a3ff"
MANIFEST_SHA = "22540dc84eb39df38566d42c025732024d586b9ca24ce72c7115d8e387997eea"
MATRIX = [("de-01", "de"), ("de-02", "de"), ("de-03", "de"), ("us-control", "us")]
FORMULA = "=B2*A2"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def inventory(root):
    return {p.relative_to(root).as_posix(): sha(p.read_bytes()) for p in sorted(root.rglob("*"))
            if p.is_file() and p.name != "raw.json"}


def expected_events(chords):
    result = []
    for chord in chords:
        result += [("KeyPress", int(code)) for code in chord]
        result += [("KeyRelease", int(code)) for code in reversed(chord)]
    return result


def main():
    evidence, source, output = map(lambda p: Path(p).resolve(), sys.argv[1:4])
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise SystemExit("STOP_AUDIT_OUTPUT_NOT_EMPTY")
    raw_bytes = (evidence / "raw.json").read_bytes()
    raw = json.loads(raw_bytes)
    manifest_bytes = (source / "research/issue_3784_explicit_x11_receiver_v1/source_manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    runner_bytes = (source / "research/issue_3784_explicit_x11_receiver_v1/runner.py").read_bytes()
    errors, fails, stops, summaries = [], [], [], []
    if raw.get("allocation") != "issue3784-explicit-x11-receiver-formal-01": errors.append("ALLOCATION")
    if raw.get("base_commit") != BASE or manifest.get("base_commit") != BASE: errors.append("BASE")
    if raw.get("image") != IMAGE: errors.append("IMAGE")
    if raw.get("runner_sha256") != RUNNER_SHA or sha(runner_bytes) != RUNNER_SHA: errors.append("RUNNER_HASH")
    if raw.get("source_manifest_sha256") != MANIFEST_SHA or sha(manifest_bytes) != MANIFEST_SHA: errors.append("MANIFEST_HASH")
    if manifest.get("candidate_blob") != "9cae101a219348077668c8fc086acf8e13154afe": errors.append("CANDIDATE_BLOB")
    for path, expected in manifest.get("files", {}).items():
        data = (source / path).read_bytes()
        if sha(data) != expected.get("sha256") or blob(data) != expected.get("git_blob_sha1"):
            errors.append("SOURCE_HASH:" + path)
    if inventory(evidence) != raw.get("artifact_sha256"): errors.append("ARTIFACT_INVENTORY")
    rows = raw.get("rows", [])
    if len(rows) != len(MATRIX):
        stops.append("INCOMPLETE_MATRIX")
    for row, (case_id, layout) in zip(rows, MATRIX):
        case = evidence / "cases" / case_id
        if row.get("case_id") != case_id or row.get("layout") != layout: errors.append("ROW_ID:" + case_id)
        if row.get("xvfb_argv", [])[-1:] != ["-noreset"]: errors.append("XVFB_NO_RESET:" + case_id)
        if row.get("xvfb_cleanup", {}).get("reaped") is not True: errors.append("XVFB_REAP:" + case_id)
        row_path = case / "row.json"
        if not row_path.is_file() or json.loads(row_path.read_text()) != row: errors.append("ROW_BINDING:" + case_id)
        recv = row.get("receiver", {})
        if recv.get("class") != "InputOnly" or recv.get("mapped") is not True: errors.append("RECEIVER_CLASS:" + case_id)
        if recv.get("event_mask") != 3: errors.append("RECEIVER_MASK:" + case_id)
        if row.get("focus_verified") is not True or recv.get("focus_window_id") != recv.get("window_id"):
            stops.append("FOCUS:" + case_id)
        control = row.get("receiver_control", [])
        control_ok = (row.get("receiver_control_ok") is True and len(control) == 2 and
                      [(x.get("type"), x.get("keycode"), x.get("lookup_text")) for x in control] ==
                      [("KeyPress", control[0].get("keycode") if control else None, "a"),
                       ("KeyRelease", control[0].get("keycode") if control else None, "a")])
        if not control_ok: stops.append("XTEST_RECEIVER_CONTROL:" + case_id)
        baseline, after = row.get("baseline", {}), row.get("after", {})
        for phase, state, expected_layout in (("baseline", baseline, "us"), ("after", after, layout)):
            q = state.get("query", {})
            if q.get("exit") != 0 or not state.get("layout_ok") or not any(
                line.strip() == "layout: " + expected_layout for line in q.get("stdout", "").splitlines()):
                stops.append("LAYOUT_QUERY:" + case_id + ":" + phase)
            dump_path, map_path = case / f"{phase}.xkb", case / f"{phase}.map.json"
            if not dump_path.is_file() or not map_path.is_file():
                errors.append("MAP_ARTIFACT_MISSING:" + case_id + ":" + phase)
                continue
            dump = dump_path.read_bytes()
            mapping = json.loads(map_path.read_text())
            if dump.decode() != state.get("dump") or sha(dump) != state.get("dump_sha256"):
                errors.append("DUMP_BINDING:" + case_id + ":" + phase)
            if mapping != state.get("map"): errors.append("MAP_BINDING:" + case_id + ":" + phase)
            map_fp = sha(json.dumps(mapping, sort_keys=True, separators=(",", ":")).encode())
            if map_fp != state.get("map_sha256"): errors.append("MAP_FINGERPRINT:" + case_id + ":" + phase)
        gate = row.get("map_gate", {})
        expected_change = layout == "de"
        if gate.get("query_layout") is not True or gate.get("dump_changed") != expected_change or gate.get("fresh_map_changed") != expected_change:
            stops.append("ACTIVE_MAP_GATE:" + case_id)
        if layout == "de" and (row.get("apply", {}).get("argv") != ["setxkbmap", "-layout", "de"] or row.get("apply", {}).get("exit") != 0):
            stops.append("LAYOUT_APPLY:" + case_id)
        if layout == "us" and row.get("apply", {}).get("argv") is not None: errors.append("CONTROL_MUTATION")
        unsupported = row.get("unsupported")
        if unsupported is None:
            (stops if row.get("status", "").startswith("STOP_") else fails).append("UNSUPPORTED_PREFLIGHT_MISSING:" + case_id)
        elif (not unsupported.get("refused_zero_event") or unsupported.get("before_events") or
              unsupported.get("after_events") or unsupported.get("emissions") != 0 or
              "U+20AC" not in str(unsupported.get("error"))):
            fails.append("UNSUPPORTED_PREFLIGHT:" + case_id)
        events = row.get("events", [])
        status = row.get("status")
        typed = ""
        if row.get("plan_keycodes") is not None:
            actual_pairs = [(e.get("type"), e.get("keycode")) for e in events]
            planned = expected_events(row.get("plan_keycodes", []))
            typed = "".join(e.get("lookup_text", "") for e in events if e.get("type") == "KeyPress")
            if actual_pairs != planned: fails.append("EVENT_TRACE:" + case_id)
            if typed != FORMULA or row.get("typed") != typed: fails.append("FORMULA_TEXT:" + case_id)
            if row.get("emissions") != len(planned): fails.append("EMISSION_COUNT:" + case_id)
            release = row.get("release", {})
            if release.get("verified") is not True or release.get("keys_down") != [] or release.get("buttons_down") != []:
                fails.append("RELEASE:" + case_id)
        if status.startswith("STOP_"): stops.append("ROW_STOP:" + case_id + ":" + status)
        elif status.startswith("FAIL_"): fails.append("ROW_FAIL:" + case_id + ":" + status)
        summaries.append({"case_id": case_id, "status": status, "receiver_control_ok": control_ok,
                          "layout_gate": gate, "typed": typed, "event_count": len(events)})
    statuses = [r.get("status") for r in rows]
    expected_disposition = ("PASS_GERMAN_FORMULA_DELIVERY" if len(rows) == 4 and all(s == "PASS_ROW" for s in statuses)
                            else "FAIL_GERMAN_FORMULA_DELIVERY" if any(s.startswith("FAIL_") for s in statuses)
                            else "STOP_GERMAN_FORMULA_DELIVERY")
    if raw.get("disposition") != expected_disposition: errors.append("DISPOSITION_BINDING")
    if errors: disposition = "FAIL_AUDIT_INTEGRITY"
    elif stops: disposition = "PASS_AUDIT_CONFIRMED_STOP"
    elif fails: disposition = "PASS_AUDIT_CONFIRMED_FAIL"
    else: disposition = "PASS_AUDIT_CONFIRMED_DELIVERY"
    audit = {"schema": "agent-interface/issue3784-audit-v1", "allocation": raw.get("allocation"),
             "raw_sha256": sha(raw_bytes), "runner_sha256": sha(runner_bytes),
             "source_manifest_sha256": sha(manifest_bytes), "artifact_count": len(inventory(evidence)),
             "raw_disposition": raw.get("disposition"), "rows": summaries, "errors": errors,
             "setup_stops": stops, "semantic_failures": fails, "disposition": disposition}
    (output / "audit.json").write_text(json.dumps(audit, sort_keys=True, indent=2, ensure_ascii=False)+"\n")
    print(json.dumps({"disposition": disposition, "errors": errors, "stops": stops, "fails": fails,
                      "rows": summaries}, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
