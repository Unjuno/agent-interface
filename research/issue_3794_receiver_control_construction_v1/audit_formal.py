from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

FORMULA = "=B2*A2"
CASES = [("de-00", "de"), ("de-01", "de"), ("de-02", "de"), ("us-control", "us")]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_xev(text: str) -> list[dict]:
    events = []
    for block in re.split(r"(?m)(?=^(?:KeyPress|KeyRelease) event,)", text):
        kind = re.match(r"(?m)^(KeyPress|KeyRelease) event,", block)
        if not kind:
            continue
        key = re.search(r"keycode\s+(\d+)\s+\(keysym\s+0x[0-9a-fA-F]+,\s*([^)]+)\)", block)
        state = re.search(r"(?m)^\s*state\s+0x([0-9a-fA-F]+)", block)
        lookup = re.search(r"XLookupString gives \d+ bytes: \(([^)]*)\)", block)
        payload = ""
        if lookup and lookup.group(1).strip():
            try:
                payload = bytes.fromhex(lookup.group(1)).decode("ascii")
            except (ValueError, UnicodeDecodeError):
                payload = "<non-ascii>"
        events.append({"type": kind.group(1), "keycode": int(key.group(1)) if key else None,
                       "keysym": key.group(2).strip() if key else None,
                       "state": int(state.group(1), 16) if state else None, "lookup_ascii": payload})
    return events


def audit(root: Path) -> dict:
    problems = []
    raw_path = root / "formal_raw.json"
    raw = json.loads(raw_path.read_text())
    manifest = json.loads(Path("research/issue_3784_focused_receiver_v1/source_manifest.json").read_text())
    freeze = json.loads(Path("research/issue_3784_focused_receiver_v1/ALLOCATION_FREEZE.json").read_text())
    if raw.get("allocation") != manifest["allocation"]:
        problems.append("allocation_mismatch")
    if raw.get("base_commit") != manifest["base_commit"]:
        problems.append("base_commit_mismatch")
    if raw.get("container_image") != manifest["container_image"]:
        problems.append("image_mismatch")
    for rel, expected in manifest["files"].items():
        if sha(Path(rel).read_bytes()) != expected:
            problems.append(f"source_hash:{rel}")
    for rel, expected in freeze["files"].items():
        if sha(Path(rel).read_bytes()) != expected:
            problems.append(f"freeze_hash:{rel}")
    if not all(raw.get("source_integrity", {}).values()) or not all(raw.get("freeze_integrity", {}).values()):
        problems.append("frozen_source_integrity")
    rows = raw.get("rows", [])
    if [r.get("case") for r in rows] != [c for c, _ in CASES]:
        problems.append("case_set_or_order")
    for row, (case, layout) in zip(rows, CASES):
        prefix = case + ":"
        if row.get("status") != "PASS":
            problems.append(prefix + "status")
            continue
        if row.get("receiver_kind") != "InputOnly" or row.get("receiver_class") != 2: problems.append(prefix + "receiver_class")
        if not row.get("focus_asserted") or row.get("focus_xid") != row.get("receiver_xid"): problems.append(prefix + "focus")
        if row.get("focus_after_backend") != row.get("receiver_xid"): problems.append(prefix + "focus_after_backend")
        if row.get("baseline_query_rc") != 0 or not re.search(r"(?m)^layout:\s+us\s*$", row.get("baseline_query", "")):
            problems.append(prefix + "baseline_us")
        baseline_dump = row.get("baseline_server_xkb_dump", "").encode()
        if (row.get("baseline_server_xkb_dump_rc") != 0 or not baseline_dump
                or sha(baseline_dump) != row.get("baseline_server_xkb_dump_sha256")):
            problems.append(prefix + "baseline_server_dump")
        if row.get("server_query_rc") != 0 or not re.search(rf"(?m)^layout:\s+{layout}\s*$", row.get("server_query", "")):
            problems.append(prefix + "server_layout")
        dump = row.get("server_xkb_dump", "").encode()
        if row.get("server_xkb_dump_rc") != 0 or not dump or sha(dump) != row.get("server_xkb_dump_sha256"):
            problems.append(prefix + "server_dump")
        if layout == "de":
            if row.get("setxkbmap", {}).get("returncode") != 0: problems.append(prefix + "layout_apply")
            if not row.get("client_core_map_changed"): problems.append(prefix + "core_map_unchanged")
            if "MappingNotify" not in row.get("receiver_mapping_events", []): problems.append(prefix + "mapping_notify")
            if not row.get("server_xkb_dump_changed"): problems.append(prefix + "server_dump_unchanged")
        elif row.get("client_core_map_changed") or row.get("server_xkb_dump_changed"):
            problems.append(prefix + "us_control_map_changed")

        control = row.get("control", {})
        c_events = control.get("events", [])
        if not control.get("pass") or [e.get("lookup_ascii") for e in c_events if e.get("type") == "KeyPress"] != ["a"]:
            problems.append(prefix + "receiver_control")
        if ([e.get("type") for e in c_events] != ["KeyPress", "KeyRelease"]
                or [e.get("keycode") for e in c_events] != [38, 38]
                or [e.get("state") for e in c_events] != [0, 0]):
            problems.append(prefix + "receiver_control_pair")
        if row.get("xev_events_before_candidate") != c_events:
            problems.append(prefix + "pre_candidate_receiver_trace")

        unsupported = row.get("unsupported", {})
        sizes = unsupported.get("receiver_log_bytes_before_after", [])
        emissions = unsupported.get("emissions_before_after", [])
        if not unsupported.get("refused") or "U+20AC" not in unsupported.get("error", ""):
            problems.append(prefix + "unsupported_not_refused")
        if emissions != [0, 0] or len(sizes) != 2 or sizes[0] != sizes[1]:
            problems.append(prefix + "unsupported_emitted")

        events = row.get("events", [])
        press = [e for e in events if e.get("type") == "KeyPress"]
        expected_count = 2 * sum(len(chord) for chord in row.get("planned_keys", []))
        if row.get("candidate") != FORMULA or "".join(e.get("lookup_ascii", "") for e in press) != FORMULA:
            problems.append(prefix + "candidate_text")
        if len(events) != expected_count or row.get("emissions") != expected_count:
            problems.append(prefix + "trace_or_emission_count")
        if any(e.get("keycode") is None for e in events): problems.append(prefix + "missing_keycode")
        expected_trace, expected_states = [], []
        for names, chord in zip(row.get("planned_keys", []), row.get("planned_keycodes", [])):
            shift_down = False
            for key, code in zip(names, chord):
                expected_trace.append(("KeyPress", code))
                expected_states.append(1 if shift_down else 0)
                if key == "SHIFT": shift_down = True
            for key, code in zip(reversed(names), reversed(chord)):
                expected_trace.append(("KeyRelease", code))
                expected_states.append(1 if shift_down else 0)
                if key == "SHIFT": shift_down = False
        observed_trace = [(e.get("type"), e.get("keycode")) for e in events]
        if observed_trace != expected_trace:
            problems.append(prefix + "press_release_trace")
        if [e.get("state") for e in events] != expected_states:
            problems.append(prefix + "modifier_state_trace")
        if row.get("held_keycodes_after") != {}: problems.append(prefix + "held_key_state")
        if row.get("candidate_preflight_emissions") != 0: problems.append(prefix + "candidate_preflight_emission")
        if row.get("xvfb_cleanup", {}).get("reaped") is not True: problems.append(prefix + "xvfb_not_reaped")

        log_path = root / "cases" / case / "xev.log"
        if not log_path.is_file():
            problems.append(prefix + "missing_receiver_log")
        else:
            data = log_path.read_bytes()
            if sha(data) != row.get("xev_log_sha256"): problems.append(prefix + "receiver_log_hash")
            observed = parse_xev(data.decode(errors="replace"))
            if observed != c_events + events:
                problems.append(prefix + "receiver_log_trace_mismatch")

    expected_decision = "PASS_FOCUSED_RECEIVER_XKB_DELIVERY_SCOPED"
    if raw.get("decision") != expected_decision:
        problems.append("decision_mismatch")
    return {"decision": "PASS_INDEPENDENT_AUDIT" if not problems else "FAIL_INDEPENDENT_AUDIT",
            "cases": len(rows), "errors": problems, "source_integrity": raw.get("source_integrity")}


if __name__ == "__main__":
    report = audit(Path(sys.argv[1]))
    Path(sys.argv[2]).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if report["decision"] == "PASS_INDEPENDENT_AUDIT" else 1)
