"""Apply the frozen health-ROI invalidator to every ordered pair of HUD frames."""
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "research/live_control"))
from policy_invalidation_guard_v1 import PolicyInvalidationGuard  # noqa: E402

RESULT_ROOT = REPO / "research/doom/results/map01-astra-attempt-v1"
BOX = [440, 585, 535, 635]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compare_pair(before, after, expected_health_changed, pair_id="pair"):
    guard = PolicyInvalidationGuard(
        {
            "op": "policy_invalidation_guard",
            "guard_id": pair_id,
            "source_sequence": 1,
            "box": BOX,
            "metric": "rgb_change",
            "rgb_threshold": 32,
            "minimum_changed_pixels": 100,
            "max_source_age_ms": 30000,
            "on_change": "needs_decision",
            "on_unknown": "needs_decision",
        },
        before,
        1,
        "map01-astra-attempt-v1",
        1_000_000_000,
    )
    outcome = guard.evaluate(after, 2, "map01-astra-attempt-v1", 1_001_000_000)
    expected = "INVALIDATED" if expected_health_changed else "UNCHANGED"
    assert outcome["status"] == expected, (
        f"{pair_id}: expected {expected}, got {outcome['status']} "
        f"({outcome['reason']}, {outcome['changed_pixels']} pixels)"
    )
    assert outcome["grants_input_authority"] is False
    assert outcome["semantic_change_identified"] is False
    assert outcome["task_success_verified"] is False
    return outcome


def verify_freeze(freeze):
    for relative, expected in freeze["inputs"].items():
        path = REPO / relative
        if sha(path) != expected["sha256"]:
            raise ValueError(f"input hash mismatch: {relative}")
    for relative, expected in freeze["code"].items():
        path = REPO / relative
        if sha(path) != expected["sha256"]:
            raise ValueError(f"source hash mismatch: {relative}")


def main():
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    verify_freeze(freeze)
    analysis = json.loads((RESULT_ROOT / "failure-analysis-v1.json").read_text())
    manifest = json.loads((RESULT_ROOT / "frame-manifest.json").read_text())
    labels = analysis["visual_transcription"]["health"]
    if len(manifest) != 13 or len(labels) != 13:
        raise ValueError("expected exactly 13 frozen frames and health labels")
    frames = []
    for row in manifest:
        with Image.open(RESULT_ROOT / row["file"]) as opened:
            frame = opened.convert("RGB")
        if sha(RESULT_ROOT / row["file"]) != row["sha256"]:
            raise ValueError(f"manifest mismatch: {row['file']}")
        frames.append(frame)

    records = []
    mismatches = 0
    for i, before in enumerate(frames):
        for j, after in enumerate(frames):
            expected_changed = labels[i] != labels[j]
            try:
                outcome = compare_pair(before, after, expected_changed, f"hud-{i:02d}-{j:02d}")
                status = outcome["status"]
                reason = outcome["reason"]
                pixels = outcome["changed_pixels"]
                passed = True
            except AssertionError as exc:
                mismatches += 1
                status = "MISMATCH"
                reason = str(exc)
                pixels = None
                passed = False
            records.append({
                "source_index": i,
                "current_index": j,
                "source_health_label": labels[i],
                "current_health_label": labels[j],
                "expected_health_changed": expected_changed,
                "status": status,
                "reason": reason,
                "changed_pixels": pixels,
                "passed": passed,
            })

    unequal = [row for row in records if row["source_index"] != row["current_index"]]
    diagonal = [row for row in records if row["source_index"] == row["current_index"]]
    summary = {
        "schema": "map01-astra-hud-pairs-a01",
        "disposition": "PASS_SCOPED" if mismatches == 0 else "FAIL_MISMATCH",
        "base_main_sha": freeze["base_main_sha"],
        "frame_count": len(frames),
        "ordered_pair_count_including_self": len(records),
        "distinct_ordered_pair_count": len(unequal),
        "self_pair_controls": len(diagonal),
        "distinct_pairs_by_same_manual_health_label": sum(not row["expected_health_changed"] for row in unequal),
        "distinct_pairs_by_changed_manual_health_label": sum(row["expected_health_changed"] for row in unequal),
        "mismatch_count": mismatches,
        "interpretation": "within-run pairwise pixel separability of the manually transcribed health label using the frozen one-way guard; not a live temporal detector evaluation",
        "limitations": [
            "one retained trajectory and 13 decision frames; pairs are dependent and do not estimate a population false-positive rate",
            "manual HUD labels and health ROI were established by the preceding posthoc analysis",
            "nonadjacent frame pairs discard temporal ordering and do not model sampling cadence, source expiry, or real-time response",
            "health change does not identify threat, direction, task effect, or safe next action",
            "no candidate, model, game, X server, OS input, or live allocation was run",
        ],
    }
    (HERE / "pairs.jsonl").write_text("".join(json.dumps(row, separators=(",", ":")) + "\n" for row in records))
    (HERE / "RESULT.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, separators=(",", ":")))


if __name__ == "__main__":
    main()
