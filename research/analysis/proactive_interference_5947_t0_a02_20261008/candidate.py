"""Deterministic authored fixture generator for Issue #8341 T0 A02.

Standard-library only. Construction code; no model, GUI, network or authority.
"""
import json
import sys
from pathlib import Path

ALLOCATION = "5947-MULTI-UPDATE-PROVENANCE-T0-A02-20261008"
DEPTHS = (0, 1, 4, 8)
ARMS = ("CURRENT_ONLY", "FULL_CONFLICTING_HISTORY", "NONCONFLICTING_HISTORY", "SOURCE_LINKED_DELTA")
CONDITIONS = ("current_value", "baseline_change", "unsupported")
PREFIX = b'{"task":"select-current","query":"what-is-the-current-value","baseline":{"value":"old","source_id":"baseline/source-17"},"current":{"value":"new","source_id":"current/source-22"},"authority":"observation-only","cue":"CURRENT", "history":['
SUFFIX = b'],"outcome":"FIXTURE_ONLY"}'
SLOT_PAD = b' ' * 512


def _history(condition, depth, arm):
    if arm == "CURRENT_ONLY" or depth == 0:
        return b""
    if arm == "FULL_CONFLICTING_HISTORY":
        return b";".join((f"episode={i};value=old{i};source=obs/{i}".encode("ascii") for i in range(depth)))
    if arm == "NONCONFLICTING_HISTORY":
        return b";".join((f"episode={i};value=neutral{i};source=obs/{i}".encode("ascii") for i in range(depth)))
    if arm == "SOURCE_LINKED_DELTA":
        return b";".join((f"episode={i};observed=old{i};superseded_by=current/source-22;kind=INFERRED".encode("ascii") for i in range(depth)))
    raise ValueError(arm)


def build_corpus():
    rows = []
    for condition in CONDITIONS:
        for depth in DEPTHS:
            for arm in ARMS:
                history = _history(condition, depth, arm)
                if len(history) > len(SLOT_PAD):
                    raise ValueError("history exceeds frozen equal-byte budget")
                slot = history + SLOT_PAD[len(history):]
                cue = PREFIX.index(b'"CURRENT"') + len(b'"CURRENT"')
                outcome = "UNKNOWN_UNSUPPORTED" if condition == "unsupported" else "SYNTHETIC_SUPPORTED"
                answer = None if condition == "unsupported" else ("new" if condition == "current_value" else "changed:old-to-new")
                rows.append({
                    "allocation": ALLOCATION, "kind": "matched", "condition": condition,
                    "depth": depth, "arm": arm, "baseline": {"value": "old", "source_id": "baseline/source-17"},
                    "baseline_source_id": "baseline/source-17", "task_bytes": b"select-current",
                    "query_bytes": condition.encode("ascii"), "prefix_bytes": PREFIX,
                    "history_slot_bytes": slot, "suffix_bytes": SUFFIX,
                    "serialized_context_bytes": PREFIX + slot + SUFFIX,
                    "history_slot_start": len(PREFIX), "history_slot_end": len(PREFIX) + len(slot),
                    "current_cue_offset": cue, "cue_byte_length": len(b'"CURRENT"'),
                    "final_truth": "new", "current_value": "new", "current_source_id": "current/source-22",
                    "authority": "observation-only", "lineage": list(range(depth)),
                    "delta_evidence": "INFERRED" if arm == "SOURCE_LINKED_DELTA" and depth else "NONE",
                    "outcome": outcome, "answer": answer,
                    "reason": "unsupported_field_without_source_evidence" if condition == "unsupported" else None,
                })
    # Separate positive-control pair. The only field changed is cue offset; the
    # serialized bytes remain fixed and carry the marker at two locations.
    base = {
        "allocation": ALLOCATION, "kind": "position_control", "condition": "baseline_change",
        "depth": 0, "arm": "CURRENT_ONLY", "baseline": {"value": "old", "source_id": "baseline/source-17"},
        "baseline_source_id": "baseline/source-17", "task_bytes": b"select-current", "query_bytes": b"baseline_change",
        "prefix_bytes": b'{"cueA":"CURRENT","cueB":"CURRENT","history":',
        "history_slot_bytes": SLOT_PAD, "suffix_bytes": b'}', "final_truth": "new", "current_value": "new",
        "current_source_id": "current/source-22", "authority": "observation-only", "lineage": [],
        "delta_evidence": "NONE", "outcome": "SYNTHETIC_SUPPORTED", "answer": "changed:old-to-new", "reason": None,
    }
    p = dict(base, serialized_context_bytes=base["prefix_bytes"] + SLOT_PAD + base["suffix_bytes"],
             history_slot_start=len(base["prefix_bytes"]), history_slot_end=len(base["prefix_bytes"]) + len(SLOT_PAD),
             current_cue_offset=base["prefix_bytes"].index(b'"CURRENT"') + 1, cue_byte_length=7)
    q = dict(p, current_cue_offset=base["prefix_bytes"].rindex(b'"CURRENT"') + 1)
    rows.extend((p, q))
    return rows


def apply_mutation(rows, mutation):
    changed = json.loads(json.dumps(rows, default=lambda value: {"__bytes__": value.hex()}))
    # Round-trip tagged byte values back into bytes so the auditor receives raw-schema types.
    def restore(value):
        if isinstance(value, dict) and set(value) == {"__bytes__"}:
            return bytes.fromhex(value["__bytes__"])
        if isinstance(value, dict):
            return {k: restore(v) for k, v in value.items()}
        if isinstance(value, list):
            return [restore(v) for v in value]
        return value
    changed = restore(changed)
    matched = [r for r in changed if r["kind"] == "matched"]
    row = matched[0]
    if mutation == "final_truth": row["final_truth"] = "forged"
    elif mutation == "baseline_identity": row["baseline_source_id"] = "forged/source"
    elif mutation == "common_byte": row["prefix_bytes"] = b"X" + row["prefix_bytes"][1:]
    elif mutation == "cue_offset": row["current_cue_offset"] += 1
    elif mutation == "lineage": row["lineage"] = []
    elif mutation == "observed_inference": row["delta_evidence"] = "OBSERVED"
    elif mutation == "unknown_answer":
        row = next(r for r in matched if r["condition"] == "unsupported"); row["answer"] = "guessed"
    elif mutation == "unsupported_omitted": changed = [r for r in changed if r["condition"] != "unsupported"]
    else: raise ValueError(mutation)
    return changed


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: candidate.py OUTPUT.json")
    out = Path(argv[1])
    if out.exists():
        raise SystemExit("STOP: output already exists")
    out.write_text(json.dumps(build_corpus(), sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv)
