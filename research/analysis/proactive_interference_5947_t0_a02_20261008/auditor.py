"""Independent raw-row auditor for Issue #8341 T0 A02.

Does not import candidate.py. Reconstructs and checks values from serialized rows.
"""
import json
import sys
from pathlib import Path

EXPECTED_CONDITIONS = {"current_value", "baseline_change", "unsupported"}
EXPECTED_ARMS = {"CURRENT_ONLY", "FULL_CONFLICTING_HISTORY", "NONCONFLICTING_HISTORY", "SOURCE_LINKED_DELTA"}
EXPECTED_DEPTHS = {0, 1, 4, 8}
EXPECTED_ALLOCATION = "5947-MULTI-UPDATE-PROVENANCE-T0-A02-20261008"


def audit_corpus(rows):
    errors = []
    matched = [r for r in rows if r.get("kind") == "matched"]
    positions = [r for r in rows if r.get("kind") == "position_control"]
    if len(rows) != 50 or len(matched) != 48 or len(positions) != 2:
        errors.append("corpus cardinality mismatch")
    groups = {}
    for r in matched:
        key = (r.get("condition"), r.get("depth"))
        groups.setdefault(key, []).append(r)
        if r.get("allocation") != EXPECTED_ALLOCATION: errors.append("allocation mismatch")
        if r.get("condition") not in EXPECTED_CONDITIONS: errors.append("unknown condition")
        if r.get("depth") not in EXPECTED_DEPTHS: errors.append("unknown depth")
        if r.get("arm") not in EXPECTED_ARMS: errors.append("unknown arm")
        if r.get("history_slot_start") != len(r.get("prefix_bytes", b"")): errors.append("slot start mismatch")
        if r.get("history_slot_end") != len(r.get("prefix_bytes", b"")) + len(r.get("history_slot_bytes", b"")): errors.append("slot end mismatch")
        expected = r.get("prefix_bytes", b"") + r.get("history_slot_bytes", b"") + r.get("suffix_bytes", b"")
        if r.get("serialized_context_bytes") != expected: errors.append("serialized context reconstruction mismatch")
        if not isinstance(r.get("baseline"), dict) or r["baseline"].get("source_id") != r.get("baseline_source_id"): errors.append("baseline identity mismatch")
        if r.get("final_truth") != "new" or r.get("current_value") != "new": errors.append("final/current truth mismatch")
        if r.get("current_source_id") != "current/source-22" or r.get("authority") != "observation-only": errors.append("current evidence/authority mismatch")
        if r.get("condition") == "unsupported":
            if r.get("outcome") != "UNKNOWN_UNSUPPORTED" or r.get("answer") is not None or not r.get("reason"):
                errors.append("unsupported query not explicit UNKNOWN")
        elif r.get("outcome") != "SYNTHETIC_SUPPORTED" or r.get("answer") is None:
            errors.append("supported query lacks authored result")
        if r.get("arm") == "SOURCE_LINKED_DELTA" and r.get("depth", 0) > 0 and r.get("delta_evidence") != "INFERRED":
            errors.append("inferred delta mislabelled")
        if r.get("arm") != "SOURCE_LINKED_DELTA" and r.get("delta_evidence") != "NONE": errors.append("unexpected delta evidence")
        if len(r.get("lineage", [])) != r.get("depth"): errors.append("lineage depth mismatch")
    if set(k[0] for k in groups) != EXPECTED_CONDITIONS or set(k[1] for k in groups) != EXPECTED_DEPTHS:
        errors.append("strata missing")
    for key, group in groups.items():
        if len(group) != 4 or {r.get("arm") for r in group} != EXPECTED_ARMS: errors.append(f"arm set mismatch {key}")
        invariant_fields = ("baseline", "baseline_source_id", "task_bytes", "query_bytes", "prefix_bytes", "suffix_bytes", "current_cue_offset", "cue_byte_length", "final_truth", "current_value", "current_source_id", "authority", "outcome", "answer", "reason")
        for field in invariant_fields:
            if len({json.dumps(r.get(field), sort_keys=True, default=lambda x: x.hex() if isinstance(x, bytes) else str(x)) for r in group}) != 1:
                errors.append(f"matched identity differs: {key} {field}")
        if len({len(r.get("serialized_context_bytes", b"")) for r in group}) != 1: errors.append(f"byte budget mismatch {key}")
    if len(positions) == 2:
        a, b = positions
        if a.get("current_cue_offset") == b.get("current_cue_offset"): errors.append("position control did not move cue")
        for field in set(a) | set(b):
            if field != "current_cue_offset" and a.get(field) != b.get(field): errors.append(f"position control changed {field}")
    return {"result": "PASS" if not errors else "FAIL", "matched_rows": len(matched), "position_rows": len(positions), "errors": errors}


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: auditor.py RAW.json RESULT.json")
    raw, output = Path(argv[1]), Path(argv[2])
    if output.exists(): raise SystemExit("STOP: audit output already exists")
    rows = json.loads(raw.read_text(encoding="utf-8"))
    result = audit_corpus(rows)
    output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["result"] == "PASS" else 1)


if __name__ == "__main__":
    main(sys.argv)
