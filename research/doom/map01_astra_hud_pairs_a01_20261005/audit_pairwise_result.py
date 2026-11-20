"""Independent raw replay and authority-boundary audit for pairwise_probe.py."""
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RESULT_ROOT = REPO / "research/doom/results/map01-astra-attempt-v1"
sys.path.insert(0, str(REPO / "research/live_control"))
from policy_invalidation_guard_v1 import PolicyInvalidationGuard  # noqa: E402

BOX = [440, 585, 535, 635]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    for section in ("inputs", "code"):
        for relative, expected in freeze[section].items():
            path = REPO / relative
            if sha(path) != expected["sha256"]:
                raise SystemExit(f"FAIL_HASH {relative}")

    analysis = json.loads((RESULT_ROOT / "failure-analysis-v1.json").read_text())
    manifest = json.loads((RESULT_ROOT / "frame-manifest.json").read_text())
    labels = analysis["visual_transcription"]["health"]
    rows = [json.loads(line) for line in (HERE / "pairs.jsonl").read_text().splitlines()]
    frames = []
    for item in manifest:
        path = RESULT_ROOT / item["file"]
        if sha(path) != item["sha256"]:
            raise SystemExit(f"FAIL_FRAME_HASH {item['file']}")
        with Image.open(path) as opened:
            frames.append(opened.convert("RGB"))

    if len(rows) != len(frames) ** 2:
        raise SystemExit(f"FAIL_PAIR_COUNT {len(rows)}")
    expected_pairs = {(i, j) for i in range(len(frames)) for j in range(len(frames))}
    seen = set()
    mismatches = []
    guard_outcomes = 0
    for row in rows:
        i, j = row["source_index"], row["current_index"]
        if (i, j) not in expected_pairs or (i, j) in seen:
            mismatches.append({"pair": [i, j], "error": "missing-or-duplicate-pair"})
            continue
        seen.add((i, j))
        changed = labels[i] != labels[j]
        spec = {
            "op": "policy_invalidation_guard", "guard_id": f"audit-{i:02d}-{j:02d}",
            "source_sequence": 1, "box": BOX, "metric": "rgb_change",
            "rgb_threshold": 32, "minimum_changed_pixels": 100,
            "max_source_age_ms": 30000, "on_change": "needs_decision",
            "on_unknown": "needs_decision",
        }
        guard = PolicyInvalidationGuard(spec, frames[i], 1, "map01-astra-attempt-v1", 1_000_000_000)
        actual = guard.evaluate(frames[j], 2, "map01-astra-attempt-v1", 1_001_000_000)
        guard_outcomes += 1
        expected_status = "INVALIDATED" if changed else "UNCHANGED"
        if (row["status"] != expected_status or row["passed"] is not True or
                row["expected_health_changed"] is not changed or
                row["changed_pixels"] != actual["changed_pixels"] or
                row["reason"] != actual["reason"] or actual["status"] != expected_status or
                actual["grants_input_authority"] is not False or
                actual["semantic_change_identified"] is not False or
                actual["task_success_verified"] is not False or
                actual["may_only_reduce_existing_authority"] is not True):
            mismatches.append({"pair": [i, j], "error": "outcome-or-authority-mismatch"})

    summary = json.loads((HERE / "RESULT.json").read_text())
    if seen != expected_pairs:
        mismatches.append({"error": "pair-set-incomplete"})
    if summary["ordered_pair_count_including_self"] != guard_outcomes:
        mismatches.append({"error": "summary-count-mismatch"})
    audit = {
        "schema": "map01-astra-hud-pairs-a01-independent-audit",
        "disposition": "PASS_AUDITED_SCOPED" if not mismatches else "FAIL_MISMATCH",
        "pair_count_recomputed": guard_outcomes,
        "unique_pairs": len(seen),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "authority_fields_rechecked": ["grants_input_authority", "semantic_change_identified", "task_success_verified", "may_only_reduce_existing_authority"],
        "scope": "independent deterministic replay of the frozen still-frame pair corpus only",
        "limits": "same guard implementation by design; manual labels and single-run nonindependence remain; no live temporal behavior or task effect is audited",
    }
    (HERE / "AUDIT.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps({k: audit[k] for k in ("disposition", "pair_count_recomputed", "mismatch_count", "scope")}))
    if mismatches:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
