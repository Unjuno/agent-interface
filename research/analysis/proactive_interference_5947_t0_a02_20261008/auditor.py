"""Independent auditor; checks raw serialized records and never imports candidate."""
import json
import sys
from pathlib import Path

CONDITIONS = {"current_value", "baseline_change", "unsupported"}
ARMS = {"CURRENT_ONLY", "FULL_CONFLICTING_HISTORY", "NONCONFLICTING_HISTORY", "SOURCE_LINKED_DELTA"}
DEPTHS = {0, 1, 4, 8}
ALLOCATION = "5947-MULTI-UPDATE-PROVENANCE-T0-A02-20261008"


def audit_corpus(rows):
    errors = []
    matched = [r for r in rows if r.get("kind") == "matched"]
    positions = [r for r in rows if r.get("kind") == "position_control"]
    if len(rows) != 50 or len(matched) != 48 or len(positions) != 2: errors.append("cardinality")
    groups = {}
    for r in matched:
        key = (r.get("condition"), r.get("depth"))
        groups.setdefault(key, []).append(r)
        if r.get("allocation") != ALLOCATION: errors.append("allocation")
        if r.get("condition") not in CONDITIONS or r.get("depth") not in DEPTHS or r.get("arm") not in ARMS: errors.append("unexpected stratum")
        try:
            prefix, slot, suffix = (bytes.fromhex(r[k]) for k in ("prefix_hex", "history_slot_hex", "suffix_hex"))
            serialized = bytes.fromhex(r["serialized_context_hex"])
            if serialized != prefix + slot + suffix: errors.append("serialized reconstruction")
            if r.get("history_slot_start") != len(prefix) or r.get("history_slot_end") != len(prefix) + len(slot): errors.append("slot offsets")
        except (KeyError, TypeError, ValueError):
            errors.append("malformed byte fields")
        try:
            baseline = json.loads(bytes.fromhex(r["baseline_bytes"]))
            if baseline.get("source_id") != r.get("baseline_source_id") or baseline != {"value": "old", "source_id": "baseline/source-17"}: errors.append("baseline object/source identity")
            current = json.loads(bytes.fromhex(r["current_bytes"]))
            if current != {"value": "new", "source_id": "current/source-22"}: errors.append("current object/source identity")
        except (KeyError, TypeError, ValueError, json.JSONDecodeError): errors.append("malformed baseline/current bytes")
        if r.get("final_truth") != "new": errors.append("final truth")
        if r.get("authority") != "observation-only": errors.append("authority")
        if r.get("lineage") != list(range(r.get("depth", -1))): errors.append("lineage depth/order")
        if r.get("arm") == "SOURCE_LINKED_DELTA" and r.get("depth", 0) and r.get("delta_evidence") != "INFERRED": errors.append("delta must remain inferred")
        if r.get("arm") != "SOURCE_LINKED_DELTA" and r.get("delta_evidence") != "NONE": errors.append("unexpected delta label")
        if r.get("condition") == "unsupported":
            if (r.get("outcome"), r.get("answer"), r.get("reason")) != ("UNKNOWN_UNSUPPORTED", None, "unsupported_field_without_source_evidence"): errors.append("unsupported is not explicit UNKNOWN")
        else:
            expected = "new" if r.get("condition") == "current_value" else "changed:old-to-new"
            if (r.get("outcome"), r.get("answer")) != ("SYNTHETIC_SUPPORTED", expected): errors.append("supported authored outcome")
    expected_keys = {(c, d) for c in CONDITIONS for d in DEPTHS}
    if set(groups) != expected_keys: errors.append("missing/extra groups")
    for key, group in groups.items():
        if len(group) != 4 or {r.get("arm") for r in group} != ARMS: errors.append(f"arm coverage {key}")
        identity = ("task_bytes", "query_bytes", "baseline_bytes", "baseline_source_id", "current_bytes", "current_source_id", "authority", "prefix_hex", "suffix_hex", "current_cue_offset", "cue_byte_length", "final_truth", "outcome", "answer", "reason")
        for field in identity:
            if len({r.get(field) for r in group}) != 1: errors.append(f"matched identity {key}:{field}")
        try:
            if len({len(bytes.fromhex(r["serialized_context_hex"])) for r in group}) != 1: errors.append(f"byte budget {key}")
        except (KeyError, TypeError, ValueError): errors.append(f"byte budget parse {key}")
    if len(positions) == 2:
        a, b = positions
        if {k for k in set(a) | set(b) if a.get(k) != b.get(k)} != {"current_cue_offset"}: errors.append("position control changed fields beyond cue offset")
    return {"result": "PASS" if not errors else "FAIL", "matched_rows": len(matched), "position_rows": len(positions), "errors": errors}


def main(argv):
    if len(argv) != 3: raise SystemExit("usage: auditor.py RAW.json RESULT.json")
    raw, output = Path(argv[1]), Path(argv[2])
    if output.exists(): raise SystemExit("STOP: audit output already exists")
    result = audit_corpus(json.loads(raw.read_text(encoding="utf-8")))
    output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["result"] == "PASS" else 1)

if __name__ == "__main__": main(sys.argv)
