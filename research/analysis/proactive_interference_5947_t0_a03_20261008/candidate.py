"""Generate the frozen synthetic matched-context A03 corpus."""
import json
import sys
from pathlib import Path


ALLOCATION = "5947-MULTI-UPDATE-PROVENANCE-T0-A03-20261008"
DEPTHS = (0, 1, 4, 8)
ARMS = ("CURRENT_ONLY", "FULL_CONFLICTING_HISTORY", "NONCONFLICTING_HISTORY", "SOURCE_LINKED_DELTA")
CONDITIONS = ("current_value", "baseline_change", "unsupported")
SLOT_SIZE = 2048
BASELINE = b'{"source_id":"baseline/source-17","value":"old"}'
CURRENT = b'{"source_id":"current/source-22","value":"new"}'
QUERIES = {
    "current_value": b"what-is-current-value",
    "baseline_change": b"did-value-change-from-baseline",
    "unsupported": b"unsupported-field-without-source-evidence",
}
SUFFIX = b'","end":"FIXTURE_ONLY"}'
POSITION_PREFIX = b'{"cueA":"CURRENT","cueB":"CURRENT","history":"'


def _history(depth, arm):
    if arm == "CURRENT_ONLY" or depth == 0:
        return b""
    if arm == "FULL_CONFLICTING_HISTORY":
        records = (f"episode={index};value=old{index};source=obs/{index}" for index in range(depth))
    elif arm == "NONCONFLICTING_HISTORY":
        records = (f"episode={index};value=neutral{index};source=obs/{index}" for index in range(depth))
    elif arm == "SOURCE_LINKED_DELTA":
        records = (
            f"episode={index};observed=old{index};superseded_by=current/source-22;kind=INFERRED"
            for index in range(depth)
        )
    else:
        raise ValueError("unsupported history arm")
    return ";".join(records).encode("ascii")


def _supported_outcome(condition):
    if condition == "current_value":
        return "SYNTHETIC_SUPPORTED", "new", None
    if condition == "baseline_change":
        return "SYNTHETIC_SUPPORTED", "changed:old-to-new", None
    if condition == "unsupported":
        return "UNKNOWN_UNSUPPORTED", None, "unsupported_field_without_source_evidence"
    raise ValueError("unsupported query condition")


def _record(condition, depth, arm, prefix, suffix, cue_offset):
    query = QUERIES[condition]
    history = _history(depth, arm)
    if len(history) > SLOT_SIZE:
        raise ValueError("history exceeds the frozen byte budget")
    slot = history + b" " * (SLOT_SIZE - len(history))
    outcome, answer, reason = _supported_outcome(condition)
    return {
        "allocation": ALLOCATION,
        "kind": "matched",
        "condition": condition,
        "depth": depth,
        "arm": arm,
        "task_bytes": b"select-current".hex(),
        "query_bytes": query.hex(),
        "baseline_bytes": BASELINE.hex(),
        "baseline_source_id": "baseline/source-17",
        "current_bytes": CURRENT.hex(),
        "current_source_id": "current/source-22",
        "authority": "observation-only",
        "current_cue_offset": cue_offset,
        "cue_byte_length": len(b"CURRENT"),
        "prefix_hex": prefix.hex(),
        "history_slot_hex": slot.hex(),
        "suffix_hex": suffix.hex(),
        "serialized_context_hex": (prefix + slot + suffix).hex(),
        "history_slot_start": len(prefix),
        "history_slot_end": len(prefix) + len(slot),
        "final_truth": "new",
        "outcome": outcome,
        "answer": answer,
        "reason": reason,
        "lineage": list(range(depth)),
        "delta_evidence": "INFERRED" if arm == "SOURCE_LINKED_DELTA" and depth else "NONE",
    }


def build_corpus():
    rows = []
    for condition in CONDITIONS:
        query = QUERIES[condition]
        prefix = (
            b'{"task":"select-current","query":"' + query +
            b'","baseline":"old","baseline_source":"baseline/source-17",'
            b'"current":"new","current_source":"current/source-22",'
            b'"authority":"observation-only","CURRENT_CUE":"CURRENT","history":"'
        )
        cue_marker = b'"CURRENT_CUE":"CURRENT"'
        cue_offset = prefix.index(cue_marker) + len(b'"CURRENT_CUE":"')
        for depth in DEPTHS:
            for arm in ARMS:
                rows.append(_record(condition, depth, arm, prefix, SUFFIX, cue_offset))

    position_slot = b" " * SLOT_SIZE
    position_offsets = (
        POSITION_PREFIX.index(b'"CURRENT"') + 1,
        POSITION_PREFIX.rindex(b'"CURRENT"') + 1,
    )
    for cue_offset in position_offsets:
        row = _record("baseline_change", 0, "CURRENT_ONLY", POSITION_PREFIX, SUFFIX, cue_offset)
        row["kind"] = "position_control"
        row["prefix_hex"] = POSITION_PREFIX.hex()
        row["history_slot_hex"] = position_slot.hex()
        row["serialized_context_hex"] = (POSITION_PREFIX + position_slot + SUFFIX).hex()
        row["history_slot_start"] = len(POSITION_PREFIX)
        row["history_slot_end"] = len(POSITION_PREFIX) + len(position_slot)
        rows.append(row)
    return rows


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: candidate.py OUTPUT.json")
    output = Path(argv[1])
    if output.exists():
        raise SystemExit("STOP: output already exists")
    output.write_text(json.dumps(build_corpus(), sort_keys=True, separators=(",", ":")) + "\n",
                       encoding="utf-8")
    print(json.dumps({"rows": 50, "allocation": ALLOCATION}, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv)
