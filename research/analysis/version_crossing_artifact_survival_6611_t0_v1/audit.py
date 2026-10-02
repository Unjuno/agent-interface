"""Independent raw-only checker for the Issue #6611 synthetic assay."""
import json
import sys
from pathlib import Path


def evaluate(fixture, raw):
    expected = fixture["expected"]
    errors = []
    controls = {"silent_formula_drop": False, "open_failure_unknown": False, "render_degradation": False,
                "cosmetic_change_accepted": False, "compact_survives_better": False}
    by_key = {(r["case_id"], r["route"]): r for r in raw.get("rows", [])}
    if raw.get("schema") != "version-crossing-raw-v1":
        errors.append("schema")
    if len(raw.get("rows", [])) != 16 or len(by_key) != 16:
        errors.append("row_denominator")
    for case in fixture["cases"]:
        for route in ("compact", "portable"):
            row = by_key.get((case["id"], route))
            if row is None:
                errors.append(f"missing:{case['id']}:{route}")
                continue
            if row.get("initial", {}).get("pass") is not True or row.get("initial", {}).get("properties") != expected:
                errors.append(f"initial_contract:{case['id']}:{route}")
            post = row.get("post", {})
            changes = dict(case.get("changes", {})); changes.update(case.get("route_changes", {}).get(route, {}))
            opened = changes.get("open", True) is True
            if not opened:
                if post.get("status") != "UNKNOWN" or any(post.get(k) is not None for k in ("value_ok", "formula_ok", "link_ok", "render_ok")):
                    errors.append(f"open_failure_not_unknown:{case['id']}:{route}")
                if case["id"] == "open-failure" and route == "portable": controls["open_failure_unknown"] = True
                if case["id"] == "compact-route-survives-better" and route == "portable": controls["compact_survives_better"] = True
                continue
            props = post.get("properties", {})
            independently_expected = dict(expected); independently_expected.update(changes)
            flags = {"value_ok": independently_expected.get("value") == expected["value"],
                     "formula_ok": independently_expected.get("formula") == expected["formula"],
                     "link_ok": independently_expected.get("link_target") == expected["link_target"],
                     "render_ok": independently_expected.get("render") == expected["render"]}
            if post.get("status") != "OBSERVED" or any(post.get(k) != v for k, v in flags.items()):
                errors.append(f"oracle_mismatch:{case['id']}:{route}")
            if any(props.get(k) != independently_expected.get(k) for k in ("value", "formula", "link_target", "render")):
                errors.append(f"property_vector:{case['id']}:{route}")
            if case["id"] == "silent-formula-drop" and route == "compact": controls["silent_formula_drop"] = post.get("formula_ok") is False
            if case["id"] == "render-only-degradation" and route == "compact": controls["render_degradation"] = post.get("render_ok") is False and post.get("value_ok") is True
            if case["id"] == "cosmetic-harmless-change" and route == "compact": controls["cosmetic_change_accepted"] = all(flags.values())
    if not all(controls.values()): errors.append("controls")
    result = {"schema": "version-crossing-audit-v1", "rows": len(raw.get("rows", [])), "controls": controls,
              "errors": errors, "disposition": "METHOD_PASS_SCOPED" if not errors else "FAIL_METHOD",
              "scope": "finite hand-authored synthetic scorer sensitivity only; no real reader/version claim"}
    return result


def main(fixture_path, raw_path, output_path):
    fixture = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
    raw = json.loads(Path(raw_path).read_text(encoding="utf-8"))
    result = evaluate(fixture, raw)
    Path(output_path).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: audit.py FIXTURE.json RAW.json AUDIT.json")
    main(*sys.argv[1:])
