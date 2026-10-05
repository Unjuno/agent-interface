"""Independent audit of the first preregistered integrated live comparison."""

import hashlib
import json
from pathlib import Path

from integrated_efficiency_protocol_v1 import ARMS, evaluate


HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "integrated-efficiency-live-01"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan, trace, report = (read(OUT / name) for name in
                           ("preregistration.json", "trace.json", "report.json"))
    for name, digest in plan["sources"].items():
        assert sha(HERE / name) == digest, name
    evaluation = evaluate(trace)
    assert evaluation == report["evaluation"]
    assert evaluation["disposition"] == "RETAIN"
    assert evaluation["observed_break_even_task"] == 2
    assert evaluation["persistent_faster_than_both_descriptive"] is True

    call_ids = []
    usage_totals = {field: 0 for field in
                    ("input_tokens", "cached_input_tokens", "cache_write_input_tokens",
                     "output_tokens", "reasoning_output_tokens")}
    for arm in ARMS:
        preflight = trace["preflight_calls"][arm]
        call_ids.append(preflight["call_id"])
        for field in usage_totals:
            usage_totals[field] += preflight["usage"][field]
        gate = read(OUT / "preflight" / arm / "gate" / "gate-report.json")
        assert gate["accepted"] is True and gate["model_calls"] == 1
        result = gate["results"][0]["result"]
        assert result["cache_hit"] is False and result["model_call_performed"] is True
        assert result["usage"] == preflight["usage"]
        rows = trace["arms"][arm]
        assert len(rows) == 6 and all(row["submission_count"] == 1
                                      and row["exact_submission"] for row in rows)
        assert sum(row["pointer_admissions"] for row in rows) == 12
        assert all(len(row["input_feedback_ns"]) == 2
                   and all(value is not None for value in row["input_feedback_ns"])
                   for row in rows)
        history = [json.loads(line) for line in
                   (OUT / "arms" / arm / "runtime" /
                    "submission-history.jsonl").read_text().splitlines()]
        assert len(history) == 6 and all(row["exact"] is True for row in history)
        assert report["independent_evaluations"][arm]["success"] is True
        for task in rows:
            for call in task["model_calls"]:
                call_ids.append(call["call_id"])
                for field in usage_totals:
                    usage_totals[field] += call["usage"][field]
    assert len(call_ids) == 17 and len(set(call_ids)) == 17
    assert len(list((OUT / "model-calls").rglob("result.json"))) == 14
    repair = trace["arms"]["persistent"][3]["repair"]
    assert repair == {"required": True, "old_reference_status": "missing",
                      "old_reference_pointer_admissions": 0,
                      "attempted": True, "succeeded": True}
    model_wait_ms = {}
    for arm in ARMS:
        details = read(OUT / "arms" / arm / "task-details.json")
        model_wait_ms[arm] = sum(
            phase["elapsed_ns"] for detail in details
            for phase in detail["adaptive"]["phase_timings"]
            if phase["stage"] in {"anchor_model", "expanded_model"}) / 1e6
    audited = {"passed": True, "disposition": evaluation["disposition"],
               "observed_break_even_task": evaluation["observed_break_even_task"],
               "all_model_calls": len(call_ids), "image_grounding_calls": 14,
               "fresh_preflight_calls": 3, "actual_usage_totals": usage_totals,
               "final_input_tokens": {arm:
                   evaluation["arms"][arm]["cumulative_input_tokens"][-1] for arm in ARMS},
               "elapsed_ms": {arm: evaluation["arms"][arm]["elapsed_ns"] / 1e6
                              for arm in ARMS},
               "image_model_wait_ms": model_wait_ms,
               "exact_tasks": {arm: 6 for arm in ARMS},
               "old_target_pointer_admissions": 0}
    (OUT / "audit.json").write_text(json.dumps(audited, indent=2) + "\n",
                                     encoding="utf-8", newline="\n")
    print(json.dumps(audited, indent=2))


if __name__ == "__main__":
    main()
