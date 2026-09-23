"""Freeze a matched archived-context visual-effect receipt decision probe."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/persistent-effect-decisions-01"
CONTEXT = HERE / "results/timing-envelope-openttd-l-11/fixed-astra"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    image = CONTEXT / "planner-7.png"
    original_prompt = CONTEXT / "prompt-7.txt"
    calibration = json.loads((HERE / "results/persistent-effect-receipt-v1-probe.json").read_text())
    receipt = next(row for row in calibration["substantial_new_effects"]
                   if row["study"] == 11 and row["drag_turn"] == 5 and row["latest_turn"] == 6)
    fields = [
        "format", "source_turn", "before_sequence", "after_sequence",
        "latest_inspection", "rgb_difference_threshold", "after_changed_pixels",
        "latest_changed_pixels", "persistent_changed_pixels", "crop_pixels",
        "persistent_fraction", "persistent_bbox_in_crop", "classification",
        "semantic_authority", "permits_new_mutation", "limit",
    ]
    compact = {field: receipt[field] for field in fields}
    baseline_prompt = original_prompt.read_text(encoding="utf-8")
    receipt_prompt = (
        baseline_prompt
        + "\nLocal visual-effect receipt from the same presented pixels. It is advisory evidence only; "
        + "apply its stated authority and limit exactly:\n"
        + json.dumps(compact, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    )
    (OUT / "baseline-prompt.txt").write_text(baseline_prompt, encoding="utf-8")
    (OUT / "receipt-prompt.txt").write_text(receipt_prompt, encoding="utf-8")
    sources = [
        "preregister_persistent_effect_decisions_v1.py",
        "run_persistent_effect_decisions_v1.py",
        "persistent_effect_receipt_v1.py",
        "probe_persistent_effect_receipt_v1.py",
        "model_pair_runner_v2.py",
        "semantic_checkpoint_v4.py",
    ]
    plan = {
        "status": "preregistered_before_model_execution",
        "design": "one frozen v11 turn7 context; same image; A/B/B/A fresh calls; B adds only one compact nonsemantic visual receipt",
        "order": ["baseline-1", "receipt-1", "receipt-2", "baseline-2"],
        "model_route": {"model": "gpt-6-astra", "effort": "medium"},
        "required_checkpoint_prior_turn": 5,
        "image": str(image),
        "image_sha256": sha(image),
        "original_prompt": str(original_prompt),
        "original_prompt_sha256": sha(original_prompt),
        "baseline_prompt_sha256": sha(OUT / "baseline-prompt.txt"),
        "receipt_prompt_sha256": sha(OUT / "receipt-prompt.txt"),
        "receipt": compact,
        "primary_endpoint": "checkpoint status distribution by condition",
        "secondary_endpoints": ["proposal kind and intent", "drag count", "reported input/cached/output tokens", "runner wall time"],
        "decision_rule": "advance to a fresh live candidate only if receipt is observed 2/2, baseline is not observed 2/2, schemas pass and no receipt call treats it as semantic authority; otherwise hold or reject",
        "failure_policy": "retain first result of every ordered call; no retry or replacement",
        "interpretation": "matched fixed-context model signal; no GUI action, correctness, speed, population or causal claim",
        "sources": {name: sha(HERE / name) for name in sources},
    }
    (OUT / "preregistration.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
