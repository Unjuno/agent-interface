"""Audit the matched persistent-effect receipt decision probe."""
import hashlib
import json
import os
from pathlib import Path

from semantic_checkpoint_v4 import parse


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/persistent-effect-decisions-01"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def local_path(value):
    value = str(value)
    if os.name != "nt" and len(value) >= 3 and value[1:3] == ":\\":
        return Path("/mnt") / value[0].lower() / value[3:].replace("\\", "/")
    return Path(value)


def proposal_and_usage(path):
    rows = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()]
    messages = [row["item"]["text"] for row in rows
                if row.get("type") == "item.completed"
                and row.get("item", {}).get("type") == "agent_message"]
    usage = [row["usage"] for row in rows if row.get("type") == "turn.completed"]
    assert len(messages) == len(usage) == 1
    return parse(messages[0], 5, "transparent"), usage[0]


def classify(proposal):
    drags = [step for step in proposal.get("steps", []) if step.get("op") == "pointer_drag"]
    return {
        "kind": proposal["kind"],
        "intent": proposal.get("intent"),
        "checkpoint_status": proposal["checkpoint"]["status"],
        "checkpoint_evidence": proposal["checkpoint"]["evidence"],
        "drag_count": len(drags),
        "drag_points": drags[0]["points"] if len(drags) == 1 else None,
    }


def main():
    plan = read(ROOT / "preregistration.json")
    assert plan["status"] == "preregistered_before_model_execution"
    assert plan["order"] == ["baseline-1", "receipt-1", "receipt-2", "baseline-2"]
    for name, expected in plan["sources"].items():
        assert sha(HERE / name) == expected, name
    image = local_path(plan["image"])
    original_prompt = local_path(plan["original_prompt"])
    assert sha(image) == plan["image_sha256"]
    assert sha(original_prompt) == plan["original_prompt_sha256"]
    assert sha(ROOT / "baseline-prompt.txt") == plan["baseline_prompt_sha256"]
    assert sha(ROOT / "receipt-prompt.txt") == plan["receipt_prompt_sha256"]
    assert (ROOT / "baseline-prompt.txt").read_bytes() == original_prompt.read_bytes()

    execution = read(ROOT / "execution.json")
    assert [row["name"] for row in execution] == plan["order"]
    assert all(row["exit_code"] == 0 and row["stderr"] == "" for row in execution)
    cases = []
    for row in execution:
        directory = ROOT / row["name"]
        proposal, usage = proposal_and_usage(directory / "events.jsonl")
        process = read(directory / "process.json")
        model_plan = read(directory / "plan.json")
        assert process["exit_code"] == 0
        assert model_plan["requested_model"] == "gpt-6-astra"
        assert model_plan["requested_effort"] == "medium"
        assert model_plan["image_sha256"] == plan["image_sha256"]
        expected_prompt = ROOT / f'{row["condition"]}-prompt.txt'
        assert sha(directory / "prompt.txt") == sha(expected_prompt)
        cases.append({
            "name": row["name"], "condition": row["condition"],
            "proposal": classify(proposal), "usage": usage,
            "runner_wall_ms": row["duration_ns"] / 1e6,
        })

    baseline = [case for case in cases if case["condition"] == "baseline"]
    receipt = [case for case in cases if case["condition"] == "receipt"]
    assert [case["proposal"]["checkpoint_status"] for case in baseline] == ["observed", "observed"]
    assert [case["proposal"]["checkpoint_status"] for case in receipt] == ["uncertain", "uncertain"]
    assert all(case["proposal"]["kind"] == "act" and case["proposal"]["intent"] == "progress"
               and case["proposal"]["drag_count"] == 1 for case in baseline)
    assert all(case["proposal"]["kind"] == "act" and case["proposal"]["intent"] == "inspect"
               and case["proposal"]["drag_count"] == 0 for case in receipt)
    archived, _ = proposal_and_usage(
        HERE / "results/timing-envelope-openttd-l-11/fixed-astra/model-7/events.jsonl")
    assert archived["checkpoint"]["status"] == "uncertain"

    total = lambda values, field: sum(case["usage"][field] for case in values)
    baseline_input = total(baseline, "input_tokens")
    receipt_input = total(receipt, "input_tokens")
    report = {
        "audit_passed": True,
        "preregistered": True,
        "cases": cases,
        "primary_endpoint": {
            "baseline": {"observed": 2, "uncertain": 0, "contradicted": 0},
            "receipt": {"observed": 0, "uncertain": 2, "contradicted": 0},
        },
        "input_tokens": {
            "baseline": baseline_input,
            "receipt": receipt_input,
            "difference": receipt_input - baseline_input,
            "difference_per_call": (receipt_input - baseline_input) / 2,
        },
        "cached_input_tokens": {
            "baseline": total(baseline, "cached_input_tokens"),
            "receipt": total(receipt, "cached_input_tokens"),
        },
        "archived_original_v11_turn7_status": archived["checkpoint"]["status"],
        "fresh_baseline_variation_detected": True,
        "live_action_executed": False,
        "decision": "REJECT_RECEIPT_V1_PROMPT_FORM;_DO_NOT_RUN_LIVE",
        "diagnosis": "the explicit no-mutation authority field appears to suppress independent visual progression as well as receipt-only authority; separate evidence description from admission semantics before retesting",
        "scope": "four matched fresh model samples on one archived image; no live correctness, speed, population, causal or general effect claim",
        "audit_sha256": sha(Path(__file__)),
    }
    (ROOT / "audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
