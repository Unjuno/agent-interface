#!/usr/bin/env python3
"""Independent data-only audit of candidate event retention output."""
import hashlib
import json
import sys
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def accepts(rows):
    try:
        if [row["event"] for row in rows] != ["typed_observation", "observation"]:
            return False
        typed, full = rows
        if typed["sequence"] != full["sequence"] or typed["capture_ns"] != full["capture_ns"]:
            return False
        if typed["signals"]["health"]["value"] != 81:
            return False
        if typed["signals"]["ammo"]["value"] != 23:
            return False
        if any(type(row["emit_ns"]) is not int for row in rows):
            return False
        if typed.get("grants_input_authority") is not False:
            return False
        return True
    except (KeyError, TypeError, IndexError):
        return False


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 audit.py OUT_DIR")
    out = Path(sys.argv[1])
    result = json.loads((out / "RESULT.json").read_text())
    package = out.parent.parent
    package_manifest = json.loads(
        (package / "PACKAGE_MANIFEST.json").read_text())
    package_controls = {
        relative: digest(package / relative) == expected
        for relative, expected in package_manifest["files"].items()
    }
    if not all(package_controls.values()):
        raise SystemExit(f"package hash mismatch: {package_controls}")
    event_path, delivered_path = out / "events.jsonl", out / "delivered.jsonl"
    if digest(event_path) != result["event_stream_sha256"]:
        raise SystemExit("event stream hash mismatch")
    if digest(delivered_path) != result["delivered_stream_sha256"]:
        raise SystemExit("delivered stream hash mismatch")
    event_rows = [json.loads(line) for line in event_path.read_text().splitlines()]
    delivered_rows = [json.loads(line) for line in delivered_path.read_text().splitlines()]
    if event_rows != delivered_rows or not accepts(event_rows):
        raise SystemExit("saved raw event rows failed independent audit")

    mutations = {}
    bad = json.loads(json.dumps(event_rows))
    bad[0]["signals"]["health"]["value"] = 82
    mutations["nested_health_value"] = bad
    bad = json.loads(json.dumps(event_rows))
    del bad[0]["signals"]["ammo"]
    mutations["missing_nested_ammo"] = bad
    mutations["missing_full_observation"] = event_rows[:1]
    mutations["reordered_events"] = list(reversed(event_rows))
    bad = json.loads(json.dumps(event_rows))
    bad[0]["emit_ns"] = True
    mutations["boolean_emit_timestamp"] = bad
    controls = {name: not accepts(rows) for name, rows in mutations.items()}
    if not all(controls.values()):
        raise SystemExit(f"mutation control accepted: {controls}")
    print(json.dumps({"result": "PASS_INDEPENDENT_RAW_AUDIT",
                      "raw_rows": len(event_rows), "controls": controls,
                      "package_hashes": package_controls}, indent=2))


if __name__ == "__main__":
    main()
