"""Independent standard-library-only raw pixel and decision audit."""
import hashlib
import json
import os
import zlib
from pathlib import Path

DATA = Path(os.environ["DATA_DIR"])
FIT = Path(os.environ["FIT_DIR"])
OUT = Path(os.environ["OUT_DIR"])


def sha(b):
    return hashlib.sha256(b).hexdigest()


def box_hit(coords, box):
    x1, y1, x2, y2 = box
    return any(x1 <= x < x2 and y1 <= y < y2 for x, y in coords)


def admission(source_present, sequence_current, format_known):
    return "INFER" if source_present and sequence_current and format_known else "YIELD"


def decide(p_irrelevant, critical, threshold=0.98):
    return "SUPPRESS" if not critical and p_irrelevant >= threshold else "FULL_FORWARD"


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    meta = json.loads((DATA / "capture.json").read_text())
    rows = [json.loads(line) for line in (DATA / "pairs.jsonl").read_text().splitlines() if line]
    result = json.loads((FIT / "result.json").read_text())
    decisions = {d["id"]: d for d in result["decisions"]}
    errors, mutations = [], {}
    fmt = meta["pixel_format"]
    bpp = fmt["bits_per_pixel"] // 8
    if bpp != 4 or meta["count"] != 120 or len(rows) != 120:
        errors.append("capture_cardinality_or_format")
    expected = 0
    o3_mismatch = 0
    false_suppressions = []
    relevant = irrelevant = suppressed_irrelevant = critical_forward = 0
    seq_ok = all(r["sequence"] == i for i, r in enumerate(rows, 1))
    for row in rows:
        before = zlib.decompress((DATA / row["before_file"]).read_bytes())
        after = zlib.decompress((DATA / row["after_file"]).read_bytes())
        expected_len = row["width"] * row["height"] * bpp
        if len(before) != expected_len or len(after) != expected_len:
            errors.append(row["id"] + ":length")
            continue
        if sha(before) != row["before_sha256"] or sha(after) != row["after_sha256"]:
            errors.append(row["id"] + ":sha256")
            continue
        changed = []
        for p in range(0, len(before), bpp):
            if before[p:p+bpp] != after[p:p+bpp]:
                idx = p // bpp
                changed.append((idx % row["width"], idx // row["width"]))
        if not changed:
            errors.append(row["id"] + ":no_pixel_delta")
        raw_relevant = box_hit(changed, row["task_roi"])
        raw_critical = box_hit(changed, row["critical_roi"])
        label_relevant = bool(row["label_relevant"])
        if raw_relevant != label_relevant:
            o3_mismatch += 1
        if row["critical"] != raw_critical:
            errors.append(row["id"] + ":critical_mask_label")
        expected += len(before) + len(after)
        if row["split"] != "heldout":
            continue
        d = decisions.get(row["id"])
        if not d:
            errors.append(row["id"] + ":missing_decision")
            continue
        threshold_decision = decide(d["p_irrelevant"], row["critical"], d["threshold"])
        if d["decision"] != threshold_decision:
            errors.append(row["id"] + ":decision_rule")
        if d["decision"] == "SUPPRESS" and (label_relevant or raw_relevant or raw_critical):
            false_suppressions.append(row["id"])
        if label_relevant:
            relevant += 1
        else:
            irrelevant += 1
            suppressed_irrelevant += d["decision"] == "SUPPRESS"
        if row["critical"] and d["decision"] == "FULL_FORWARD" and d["reason"] == "critical_override":
            critical_forward += 1
    mutations["all_source_frames_hash_and_zlib_roundtrip"] = not errors
    mutations["missing_source_yields"] = admission(False, True, True) == "YIELD"
    mutations["stale_sequence_yields"] = seq_ok and admission(True, False, True) == "YIELD"
    mutations["ambiguous_pixel_format_yields"] = fmt["bits_per_pixel"] == 32 and admission(True, True, False) == "YIELD"
    mutations["critical_roi_forces_full_forward"] = critical_forward == sum(r["split"] == "heldout" and r["critical"] for r in rows)
    mutations["threshold_mutation_detected"] = any(
        decide(d["p_irrelevant"], d["critical"], threshold=0.0) != d["decision"]
        for d in result["decisions"]
    )
    heldout = [r for r in rows if r["split"] == "heldout"]
    train_families = sorted({r["family"] for r in rows if r["split"] == "train"})
    test_families = sorted({r["family"] for r in heldout})
    if train_families != [0, 1, 2, 3] or test_families != [4, 5]:
        errors.append("family_split")
    if set(decisions) != {r["id"] for r in heldout}:
        errors.append("decision_set_mismatch")
    if o3_mismatch:
        errors.append("raw_o3_label_mismatch:" + str(o3_mismatch))
    if false_suppressions:
        errors.append("false_suppressions:" + ",".join(false_suppressions))
    if irrelevant != 16 or relevant != 24:
        errors.append("heldout_class_cardinality")
    if suppressed_irrelevant < 8:
        errors.append("irrelevant_utility_below_50_percent")
    if critical_forward != 8:
        errors.append("critical_override_count")
    if not all(mutations.values()):
        errors.append("mutation_control_failed")
    audit = {"schema": "issue-4799-raw-audit-v1", "decision": "PASS_RAW_AUDIT" if not errors else "FAIL_RAW_AUDIT",
             "errors": errors, "raw_frame_bytes_verified": expected, "pairs": len(rows),
             "train_families": train_families, "heldout_families": test_families,
             "heldout_relevant_or_critical": relevant, "heldout_clear_irrelevant": irrelevant,
             "suppressed_irrelevant": suppressed_irrelevant,
             "irrelevant_suppression_rate": suppressed_irrelevant / irrelevant if irrelevant else 0,
             "false_suppressions": false_suppressions, "critical_full_forward": critical_forward,
             "o3_label_mismatches": o3_mismatch, "mutation_controls": mutations,
             "scope": "synthetic Tk/X11 fixture; not runtime authority or product transfer"}
    (OUT / "audit.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
    print(json.dumps(audit, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

