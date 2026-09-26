"""Independent read-only-input audit of Issue #3764 map diagnostic artifacts."""
import hashlib
import json
from pathlib import Path
import re
import sys

BASE = "4b2e84b79633281138b6f72c70e98d5fe9a5bf95"
RUNNER_SHA256 = "e726578c43725060bcafb4fd65cd39d3735b727a4fa3c606f70d6f23b02284e2"
CASES = [("de-01", "de"), ("de-02", "de"), ("de-03", "de"), ("us-control", "us")]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def inventory(root):
    return {p.relative_to(root).as_posix(): sha(p.read_bytes())
            for p in sorted(root.rglob("*")) if p.is_file() and p.name != "raw.json"}


def fingerprint(mapping):
    encoded = json.dumps(mapping, sort_keys=True, separators=(",", ":")).encode()
    return sha(encoded)


def symbol_rows(mapping):
    from Xlib import XK
    wanted = {XK.string_to_keysym(name): name
              for name in ("y", "Y", "z", "Z", "equal", "asterisk")}
    found = {name: [] for name in sorted(wanted.values())}
    for offset, row in enumerate(mapping["rows"]):
        for level, value in enumerate(row):
            name = wanted.get(int(value))
            if name is not None:
                found[name].append({"keycode": mapping["min_keycode"] + offset,
                                    "level": level, "keysym": int(value)})
    return found


def main():
    evidence, source, result_dir = [Path(x).resolve() for x in sys.argv[1:4]]
    result_dir.mkdir(parents=True, exist_ok=True)
    if any(result_dir.iterdir()):
        raise SystemExit("STOP_AUDIT_OUTPUT_NOT_EMPTY")
    raw_path = evidence / "raw.json"
    raw_bytes = raw_path.read_bytes()
    raw = json.loads(raw_bytes)
    runner_bytes = (source / "research/integration/issue_3764_xkb_map_diagnostic_v1/runner.py").read_bytes()
    errors = []
    if raw.get("allocation") != "issue3733-german-xkb-map-diagnostic-formal-01": errors.append("ALLOCATION_ID")
    if raw.get("base_commit") != BASE: errors.append("BASE_MISMATCH")
    if raw.get("runner_sha256") != RUNNER_SHA256 or sha(runner_bytes) != RUNNER_SHA256: errors.append("RUNNER_HASH")
    actual_inventory = inventory(evidence)
    if raw.get("artifact_sha256") != actual_inventory: errors.append("ARTIFACT_INVENTORY")
    if len(raw.get("rows", [])) != len(CASES): errors.append("ROW_COUNT")
    summaries = []
    for row, (case_id, layout) in zip(raw.get("rows", []), CASES):
        if row.get("case_id") != case_id or row.get("layout") != layout: errors.append(f"ROW_ID:{case_id}")
        if row.get("status") != "CAPTURED": errors.append(f"ROW_NOT_CAPTURED:{case_id}")
        expected_display = f":{171 + len(summaries)}"
        if row.get("display") != expected_display or row.get("xvfb_argv") != ["Xvfb", expected_display, "-screen", "0", "800x600x24", "-nolisten", "tcp", "-noreset"]:
            errors.append(f"XVFB_CONTRACT:{case_id}")
        case_dir = evidence / "cases" / case_id
        if row.get("case_artifacts_sha256") != inventory(case_dir): errors.append(f"CASE_INVENTORY:{case_id}")
        for phase in ("baseline", "after"):
            state = row.get(phase, {})
            query_path = case_dir / f"{phase}.setxkbmap.json"
            xkb_path = case_dir / f"{phase}.xkbcomp.stdout"
            if not query_path.is_file() or not xkb_path.is_file():
                errors.append(f"CAPTURE_FILE_MISSING:{case_id}:{phase}")
                continue
            query = json.loads(query_path.read_text())
            xkb_bytes = xkb_path.read_bytes()
            if query != state.get("setxkbmap"): errors.append(f"QUERY_BINDING:{case_id}:{phase}")
            if query.get("argv") != ["setxkbmap", "-query", "-display", expected_display]: errors.append(f"QUERY_COMMAND:{case_id}:{phase}")
            if state.get("xkbcomp", {}).get("exit") == 0 and state.get("xkbcomp", {}).get("argv") != ["xkbcomp", "-xkb", expected_display, "-"]:
                errors.append(f"XKBCOMP_COMMAND:{case_id}:{phase}")
            if state.get("xkbcomp", {}).get("stdout_sha256") != sha(xkb_bytes): errors.append(f"XKBCOMP_HASH:{case_id}:{phase}")
            if query.get("exit") != 0 or state.get("xkbcomp", {}).get("exit") != 0: errors.append(f"QUERY_EXIT:{case_id}:{phase}")
            for index in (1, 2):
                xlib = state.get(f"xlib_{index}", {})
                file_path = case_dir / f"{phase}.xlib-{index}.json"
                if not file_path.is_file() or json.loads(file_path.read_text()) != xlib:
                    errors.append(f"XLIB_FILE_BINDING:{case_id}:{phase}:{index}")
                mapping = xlib.get("mapping", {})
                if xlib.get("sha256") != fingerprint(mapping): errors.append(f"XLIB_FINGERPRINT:{case_id}:{phase}:{index}")
                if xlib.get("symbols") != symbol_rows(mapping): errors.append(f"XLIB_SYMBOLS:{case_id}:{phase}:{index}")
            if phase == "baseline":
                expected = "us"
            else:
                expected = layout
            if not re.search(rf"(?m)^layout:\s+{re.escape(expected)}\s*$", query.get("stdout", "")):
                errors.append(f"LAYOUT_QUERY:{case_id}:{phase}")
        if row.get("xvfb_cleanup", {}).get("reaped") is not True: errors.append(f"XVFB_NOT_REAPED:{case_id}")
        comparison = row.get("comparison", {})
        baseline = row.get("baseline", {})
        after = row.get("after", {})
        xkb_changed = baseline.get("xkbcomp", {}).get("stdout_sha256") != after.get("xkbcomp", {}).get("stdout_sha256")
        xlib_changed = baseline.get("xlib_1", {}).get("sha256") != after.get("xlib_1", {}).get("sha256")
        if comparison.get("xkbcomp_dump_changed") != xkb_changed or comparison.get("xlib_core_map_changed") != xlib_changed:
            errors.append(f"CHANGE_COMPARISON:{case_id}")
        if comparison.get("xlib_fresh_connections_agree_baseline") != (baseline.get("xlib_1", {}).get("sha256") == baseline.get("xlib_2", {}).get("sha256")):
            errors.append(f"FRESH_BASELINE_COMPARISON:{case_id}")
        if comparison.get("xlib_fresh_connections_agree_after") != (after.get("xlib_1", {}).get("sha256") == after.get("xlib_2", {}).get("sha256")):
            errors.append(f"FRESH_AFTER_COMPARISON:{case_id}")
        if comparison.get("server_layout_matches_requested") is not True: errors.append(f"REQUESTED_LAYOUT:{case_id}")
        if not row.get("apply", {}).get("exit") == 0: errors.append(f"LAYOUT_APPLY:{case_id}")
        expected_apply = (["setxkbmap", "-display", expected_display, "-layout", "de"]
                          if layout == "de" else None)
        if row.get("apply", {}).get("argv") != expected_apply: errors.append(f"LAYOUT_APPLY_COMMAND:{case_id}")
        summaries.append({"case_id": case_id, "layout": layout, "xkbcomp_dump_changed": xkb_changed,
                          "xlib_core_map_changed": xlib_changed,
                          "fresh_connections_agree": comparison.get("xlib_fresh_connections_agree_after")})
    if len(summaries) == len(CASES):
        xkb_mismatch = any(item["xkbcomp_dump_changed"] != item["xlib_core_map_changed"]
                           for item in summaries if item["layout"] == "de")
        fresh_mismatch = any(item["fresh_connections_agree"] is not True for item in summaries)
        expected_disposition = ("STOP_FRESH_CLIENT_QUERY_DISAGREEMENT" if fresh_mismatch else
                                "STOP_SERVER_CLIENT_MAP_DISAGREEMENT" if xkb_mismatch else
                                "PASS_DIAGNOSTIC")
        if raw.get("disposition") != expected_disposition: errors.append("DISPOSITION_MISMATCH")
    if actual_inventory.get("raw.json") is not None: errors.append("RAW_INCLUDED_IN_INVENTORY")
    audit = {"schema": "agent-interface/issue3764-xkb-map-audit-v1",
             "allocation": raw.get("allocation"), "raw_sha256": sha(raw_bytes),
             "runner_sha256": sha(runner_bytes), "actual_artifact_count": len(actual_inventory),
             "rows": summaries, "raw_disposition": raw.get("disposition"), "errors": errors,
             "disposition": ("PASS_AUDIT_CONFIRMED_DIAGNOSTIC" if not errors and raw.get("disposition") == "PASS_DIAGNOSTIC"
                             else "PASS_AUDIT_CONFIRMED_STOP" if not errors else "FAIL_AUDIT")}
    (result_dir / "audit.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"disposition": audit["disposition"], "raw_disposition": audit["raw_disposition"],
                      "errors": errors, "rows": summaries}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
