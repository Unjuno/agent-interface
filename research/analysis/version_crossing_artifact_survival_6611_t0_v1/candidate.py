"""Finite synthetic version-crossing artifact assay (Issue #6611)."""
import json
import sys
from pathlib import Path


def main(fixture_path, output_path):
    fixture = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
    expected = fixture["expected"]
    rows = []
    for case in fixture["cases"]:
        for route in ("compact", "portable"):
            properties = dict(expected)
            changes = dict(case.get("changes", {}))
            changes.update(case.get("route_changes", {}).get(route, {}))
            properties.update(changes)
            opened = properties.get("open") is True
            initial_properties = fixture["routes"][route]["initial_properties"]
            initial_pass = all(initial_properties.get(k) == expected[k] for k in ("value", "formula", "link_target", "render"))
            if opened:
                post = {
                    "status": "OBSERVED",
                    "value_ok": properties.get("value") == expected["value"],
                    "formula_ok": properties.get("formula") == expected["formula"],
                    "link_ok": properties.get("link_target") == expected["link_target"],
                    "render_ok": properties.get("render") == expected["render"],
                    "properties": {k: properties.get(k) for k in ("value", "formula", "link_target", "render")},
                    "metadata_order": properties.get("metadata_order"),
                    "theme": properties.get("theme")
                }
            else:
                post = {"status": "UNKNOWN", "reason": "reader_open_failed", "value_ok": None, "formula_ok": None, "link_ok": None, "render_ok": None}
            rows.append({"case_id": case["id"], "route": route, "initial": {"pass": initial_pass, "properties": initial_properties},
                         "post": post, "total_cost": fixture["acquisition_cost"][route] + fixture["reader_reopen_cost"][route]})
    raw = {"schema": "version-crossing-raw-v1", "rows": rows}
    Path(output_path).write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"schema": raw["schema"], "row_count": len(rows), "output": str(output_path)}, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: candidate.py FIXTURE.json RAW.json")
    main(sys.argv[1], sys.argv[2])
