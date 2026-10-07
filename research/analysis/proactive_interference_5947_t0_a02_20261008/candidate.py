"""Deterministic synthetic generator for Issue #8341 T0 A02; stdlib only."""
import json
import sys
from pathlib import Path

ALLOCATION = "5947-MULTI-UPDATE-PROVENANCE-T0-A02-20261008"
DEPTHS = (0, 1, 4, 8)
ARMS = ("CURRENT_ONLY", "FULL_CONFLICTING_HISTORY", "NONCONFLICTING_HISTORY", "SOURCE_LINKED_DELTA")
CONDITIONS = ("current_value", "baseline_change", "unsupported")
SLOT_SIZE = 2048
SUFFIX = b'","end":"FIXTURE_ONLY"}'
BASELINE = b'{"value":"old","source_id":"baseline/source-17"}'
CURRENT = b'{"value":"new","source_id":"current/source-22"}'


def history(condition, depth, arm):
    if arm == "CURRENT_ONLY" or depth == 0: return b""
    if arm == "FULL_CONFLICTING_HISTORY":
        return b";".join(f"episode={i};value=old{i};source=obs/{i}".encode("ascii") for i in range(depth))
    if arm == "NONCONFLICTING_HISTORY":
        return b";".join(f"episode={i};value=neutral{i};source=obs/{i}".encode("ascii") for i in range(depth))
    return b";".join(f"episode={i};observed=old{i};superseded_by=current/source-22;kind=INFERRED".encode("ascii") for i in range(depth))


def row(condition, depth, arm):
    query = {"current_value": b"what-is-current-value", "baseline_change": b"did-value-change-from-baseline", "unsupported": b"unsupported-field-without-source-evidence"}[condition]
    prefix = (b'{"task":"select-current","query":"' + query +
              b'","baseline":"old","baseline_source":"baseline/source-17","current":"new","current_source":"current/source-22","authority":"observation-only","CURRENT_CUE":"CURRENT","history":"')
    h = history(condition, depth, arm)
    if len(h) > SLOT_SIZE: raise ValueError("history exceeds frozen slot")
    slot = h + b" " * (SLOT_SIZE - len(h))
    unsupported = condition == "unsupported"
    return {
        "allocation": ALLOCATION, "kind": "matched", "condition": condition, "depth": depth, "arm": arm,
        "task_bytes": b"select-current".hex(), "query_bytes": query.hex(),
        "baseline_bytes": BASELINE.hex(), "baseline_source_id": "baseline/source-17",
        "current_bytes": CURRENT.hex(), "current_source_id": "current/source-22", "authority": "observation-only",
        "current_cue_offset": prefix.index(b'"CURRENT_CUE":"CURRENT"') + len(b'"CURRENT_CUE":"'),
        "cue_byte_length": len(b'CURRENT'), "prefix_hex": prefix.hex(), "history_slot_hex": slot.hex(),
        "suffix_hex": SUFFIX.hex(), "serialized_context_hex": (prefix + slot + SUFFIX).hex(),
        "history_slot_start": len(prefix), "history_slot_end": len(prefix) + len(slot),
        "final_truth": "new", "outcome": "UNKNOWN_UNSUPPORTED" if unsupported else "SYNTHETIC_SUPPORTED",
        "answer": None if unsupported else ("new" if condition == "current_value" else "changed:old-to-new"),
        "reason": "unsupported_field_without_source_evidence" if unsupported else None,
        "lineage": list(range(depth)), "delta_evidence": "INFERRED" if arm == "SOURCE_LINKED_DELTA" and depth else "NONE",
    }


def build_corpus():
    rows = [row(c, d, a) for c in CONDITIONS for d in DEPTHS for a in ARMS]
    prefix = b'{"cueA":"CURRENT","cueB":"CURRENT","history":"'
    slot, suffix = b" " * SLOT_SIZE, b'","end":"FIXTURE_ONLY"}'
    common = {
        "allocation": ALLOCATION, "kind": "position_control", "condition": "baseline_change", "depth": 0, "arm": "CURRENT_ONLY",
        "task_bytes": b"select-current".hex(), "query_bytes": b"baseline_change".hex(),
        "baseline_bytes": BASELINE.hex(), "baseline_source_id": "baseline/source-17",
        "current_bytes": CURRENT.hex(), "current_source_id": "current/source-22", "authority": "observation-only",
        "cue_byte_length": len(b'"CURRENT"'), "prefix_hex": prefix.hex(), "history_slot_hex": slot.hex(), "suffix_hex": suffix.hex(),
        "serialized_context_hex": (prefix + slot + suffix).hex(), "history_slot_start": len(prefix), "history_slot_end": len(prefix) + len(slot),
        "final_truth": "new", "outcome": "SYNTHETIC_SUPPORTED", "answer": "changed:old-to-new", "reason": None,
        "lineage": [], "delta_evidence": "NONE",
    }
    rows.extend((dict(common, current_cue_offset=prefix.index(b'CURRENT')),
                 dict(common, current_cue_offset=prefix.rindex(b'CURRENT'))))
    return rows


def main(argv):
    if len(argv) != 2: raise SystemExit("usage: candidate.py OUTPUT.json")
    output = Path(argv[1])
    if output.exists(): raise SystemExit("STOP: output already exists")
    output.write_text(json.dumps(build_corpus(), sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")

if __name__ == "__main__": main(sys.argv)
