#!/usr/bin/env python3
"""Independent arithmetic/identity check of A01's saved raw table."""
import hashlib
import json
import sys
from pathlib import Path

raw_path = Path(sys.argv[1])
raw = json.loads(raw_path.read_text())
errors = []
if raw.get("format") != "astra_visible_effect_probe_a01_v1": errors.append("format")
if raw.get("source_video_sha256") != "201ab6aaa8ab5823285b44864ad1df899ebe5a19c97ec6e84b8cc5db063f6be4": errors.append("source_hash")
rows = raw.get("rows")
if type(rows) is not list or len(rows) != 10: errors.append("row_count")
if raw.get("frame_count") != 10: errors.append("frame_count")
if raw.get("threshold") != 40: errors.append("threshold")
if isinstance(rows, list):
    for i, row in enumerate(rows):
        if row.get("frame") != i: errors.append(f"frame_index_{i}")
        if abs(row.get("video_time_s", -999) - (21.5 + .2*i)) > .002: errors.append(f"timestamp_{i}")
        expected = (i > 0 and row.get("new_warm_pixels", -1) >= 40)
        if row.get("trigger") is not expected: errors.append(f"trigger_reconstruction_{i}")
base = [r for r in rows if r["trigger"] and r["video_time_s"] < 22.0]
window = [r for r in rows if r["trigger"] and 22.0 <= r["video_time_s"] < 23.5]
first = next((r["video_time_s"] for r in rows if r["trigger"]), None)
# The frozen rule is conjunctive; any pre-window cue rejects enemy-specific feasibility.
disposition = "FAIL_FIXED_RULE_PREWINDOW_TRIGGER" if base else ("PASS_SCOPED_CUE" if window else "FAIL_NO_EARLY_TRIGGER")
out = {"status": "PASS_RAW_RECONSTRUCTION" if not errors else "FAIL_RAW_RECONSTRUCTION",
       "errors": errors, "row_count": len(rows), "first_trigger_video_s": first,
       "pre_window_trigger_count": len(base), "in_window_trigger_count": len(window),
       "disposition": disposition,
       "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
       "scope": "independent arithmetic and freeze-identity reconstruction only; not semantic image labels"}
print(json.dumps(out, indent=2))
Path(raw_path.parent, "AUDIT.json").write_text(json.dumps(out, indent=2)+"\n")
if errors: raise SystemExit(1)
