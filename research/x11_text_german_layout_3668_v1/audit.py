#!/usr/bin/env python3
"""Independent finite audit for issue 3733 X11 text delivery rows."""
import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_BACKEND_BLOB = "9cae101a219348077668c8fc086acf8e13154afe"
FORMULA = "=B2*A2"
REQUIRED = ["de-01.json", "de-02.json", "de-03.json", "us-control.json"]


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def check_row(path, requested_layout):
    row = json.loads(path.read_text(encoding="utf-8"))
    errors = []
    if row.get("status") != "ROW_RECORDED":
        errors.append("row status is not ROW_RECORDED")
    if row.get("allocation") != "issue3668-german-xkb-text-v1":
        errors.append("allocation identity mismatch")
    if row.get("backend_git_blob") != EXPECTED_BACKEND_BLOB:
        errors.append("backend source blob mismatch")
    if row.get("formula") != FORMULA or row.get("decoded_formula") != FORMULA:
        errors.append("decoded formula mismatch")
    before, after = row.get("before", {}), row.get("after", {})
    before_layout = before.get("layout", {}).get("layout")
    after_layout = after.get("layout", {}).get("layout")
    if before_layout != "us":
        errors.append("fresh Xvfb baseline was not US")
    if after_layout != requested_layout:
        errors.append("requested layout not active after setup")
    before_maps, after_maps = before.get("maps", {}), after.get("maps", {})
    for key in ("server_xkb", "core_keymap", "modifier_map"):
        left, right = before_maps.get(key), after_maps.get(key)
        if type(left) is not str or type(right) is not str:
            errors.append(f"raw {key} map missing")
        elif requested_layout == "de" and left == right:
            errors.append(f"{key} did not change for German layout")
        elif requested_layout == "us" and left != right:
            errors.append(f"{key} unexpectedly changed in US control")
    if row.get("xkb_extension") is not True:
        errors.append("XKEYBOARD extension unavailable")
    if row.get("unsupported_refused") is not True:
        errors.append("late unsupported text was not refused")
    if "U+20AC" not in row.get("unsupported_error", ""):
        errors.append("late unsupported error not exact")
    if row.get("unsupported_emissions_before") != 0 or row.get("unsupported_emissions_after") != 0:
        errors.append("unsupported case emitted input")
    if row.get("receiver_events_before_delivery") != 0:
        errors.append("receiver observed events before the single valid delivery")
    plan = row.get("planned_chords")
    if type(plan) is not list or len(plan) != len(FORMULA):
        errors.append("text plan length mismatch")
    else:
        if type(row.get("emissions_for_formula")) is not int:
            errors.append("formula emission count missing")
        elif row["emissions_for_formula"] != 2 * sum(len(chord) for chord in plan):
            errors.append("formula press/release emission count mismatch")
        for char, symbol_name, offset in (("=", "equal", 0), ("*", "asterisk", 3)):
            sym = row.get("symbol_levels", {}).get(char, {})
            selected = sym.get("selected_level")
            if selected not in (0, 1) or sym.get("keysym_name") != symbol_name:
                errors.append(f"{char} not found at an admitted level")
            expected_chord = [symbol_name] if selected == 0 else ["SHIFT", symbol_name]
            if plan and plan[offset] != expected_chord:
                errors.append(f"{char} planner chord disagrees with active keymap")
    received = row.get("received_keypresses")
    if type(received) is not list or len(received) < len(FORMULA):
        errors.append("too few received XTEST keypresses")
    if row.get("tracked_held_keys_after") != []:
        errors.append("backend reports keys still held")
    state = row.get("key_state_after", {})
    if not state or any(value is not False for value in state.values()):
        errors.append("one or more planned keys remain physically down")
    return {"file": path.name, "layout": requested_layout, "errors": errors,
            "row_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "server_xkb_before_sha256": digest(before_maps.get("server_xkb", "")),
            "server_xkb_after_sha256": digest(after_maps.get("server_xkb", "")),
            "decoded_formula": row.get("decoded_formula"),
            "emissions": row.get("emissions_for_formula")}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("results", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for name in REQUIRED:
        path = args.results / name
        if not path.is_file():
            rows.append({"file": name, "errors": ["required run row missing"]})
            continue
        layout = "us" if name == "us-control.json" else "de"
        rows.append(check_row(path, layout))
    errors = [f"{row['file']}: {error}" for row in rows for error in row.get("errors", [])]
    result = {
        "allocation": "issue3668-german-xkb-text-v1",
        "status": "PASS_GERMAN_XKB_TEXT_DELIVERY_SCOPED" if not errors else "FAIL_AUDIT",
        "expected_backend_git_blob": EXPECTED_BACKEND_BLOB,
        "required_rows": REQUIRED,
        "rows": rows,
        "errors": errors,
        "scope": "private Xvfb XTEST only; no Calc/model/host-display or container claim",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
