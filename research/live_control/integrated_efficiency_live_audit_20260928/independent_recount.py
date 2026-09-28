"""Independent filesystem-level recount; does not import project evaluators."""
import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(sys.argv[1])
OUT = Path(sys.argv[2])
FREEZE_PATH = Path(sys.argv[3])
EVIDENCE = ROOT / "research/live_control/results/integrated-efficiency-live-01"
ARMS = ("plain", "ephemeral", "persistent")
USAGE = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens",
         "output_tokens", "reasoning_output_tokens")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def main():
    freeze = read(FREEZE_PATH)
    files = {name: EVIDENCE / name for name in
             ("preregistration.json", "trace.json", "report.json", "audit.json")}
    for name, digest_key in (("preregistration.json", "preregistration_sha256"),
                             ("trace.json", "trace_sha256"),
                             ("report.json", "report_sha256"),
                             ("audit.json", "existing_audit_sha256")):
        require(sha(files[name]) == freeze[digest_key], f"frozen digest mismatch: {name}")
    prereg, trace, report, stored = (read(files[n]) for n in
                                    ("preregistration.json", "trace.json", "report.json", "audit.json"))
    require(prereg["study"] == "integrated-efficiency-live-01", "study identity mismatch")

    # Raw-call population is taken from the terminal call records, then matched
    # to trace descriptors by ID; cached tokens remain a subset of input.
    raw_calls = {}
    for arm in ARMS:
        gate = read(EVIDENCE / "preflight" / arm / "gate" / "gate-report.json")
        require(gate["accepted"] is True and gate["model_calls"] == 1,
                f"preflight gate invalid: {arm}")
        result = gate["results"][0]["result"]
        require(result["cache_hit"] is False and result["model_call_performed"] is True,
                f"preflight not fresh: {arm}")
        require(result["model_call_performed"] is True and result["cache_hit"] is False,
                f"preflight was not a fresh model call: {arm}")
        for path in (EVIDENCE / "model-calls" / arm).rglob("result.json"):
            data = read(path)
            require(data.get("call_id") and data.get("usage"), f"raw result missing call/usage: {path}")
            raw_calls[data["call_id"]] = data["usage"]
    require(len(raw_calls) == 14, f"expected 14 raw image calls, got {len(raw_calls)}")

    trace_calls = {}
    class_totals = {arm: {field: 0 for field in USAGE} for arm in ARMS}
    cumulative_input, cumulative_generations = {}, {}
    preflight_by_arm = {arm: read(EVIDENCE / "preflight" / arm / "gate" / "gate-report.json")
                        ["results"][0]["result"]["usage"]["input_tokens"] for arm in ARMS}
    task_counts, submission_counts = {}, {}
    for arm in ARMS:
        pf = trace["preflight_calls"][arm]
        require(pf["usage"] == read(EVIDENCE / "preflight" / arm / "gate" / "gate-report.json")
                ["results"][0]["result"]["usage"], f"preflight usage mismatch: {arm}")
        rows = trace["arms"][arm]
        require(len(rows) == 6, f"task count mismatch: {arm}")
        task_counts[arm] = len(rows)
        cumulative_input[arm] = []
        cumulative_generations[arm] = []
        used_input = 0
        generations = 1  # one fresh schema-preflight model generation per arm
        for index, task in enumerate(rows, 1):
            require(task["task_id"] == f"task-{index}", f"order mismatch: {arm}/{index}")
            require(task["exact_submission"] is True and task["submission_count"] == 1,
                    f"trace submission failure: {arm}/{index}")
            require(task["releases_verified"] is True, f"release missing: {arm}/{index}")
            used_input += sum(call["usage"]["input_tokens"] for call in task["model_calls"])
            generations += task["planner_generations"]
            cumulative_input[arm].append(used_input + preflight_by_arm[arm])
            cumulative_generations[arm].append(generations)
            for call in task["model_calls"]:
                cid = call["call_id"]
                require(cid not in trace_calls, f"duplicate trace call ID: {cid}")
                trace_calls[cid] = call["usage"]
                for field in USAGE:
                    class_totals[arm][field] += call["usage"][field]
        history = [json.loads(line) for line in
                   (EVIDENCE / "arms" / arm / "runtime" / "submission-history.jsonl")
                   .read_text(encoding="utf-8").splitlines() if line.strip()]
        require(len(history) == 6, f"history count mismatch: {arm}")
        require(all(row["exact"] is True and row["task_id"] == f"task-{i}"
                    for i, row in enumerate(history, 1)), f"history exact/order mismatch: {arm}")
        submission_counts[arm] = len(history)

    require(len(trace_calls) == 14, f"expected 14 trace image calls, got {len(trace_calls)}")
    require(set(trace_calls) == set(raw_calls), "trace/raw call ID population mismatch")
    for cid in trace_calls:
        require(trace_calls[cid] == raw_calls[cid], f"raw usage mismatch: {cid}")
    image_ids = list(trace_calls)
    require(len(image_ids) == 14 and len(set(image_ids)) == 14,
            "expected 14 globally unique image-call IDs")

    preflight_totals = {field: sum(trace["preflight_calls"][arm]["usage"][field]
                                   for arm in ARMS) for field in USAGE}
    totals = {field: preflight_totals[field] + sum(v[field] for v in class_totals.values())
              for field in USAGE}
    stored_totals = stored["actual_usage_totals"]
    require(totals == stored_totals, "aggregate usage differs from stored independent audit")
    report_eval = report["evaluation"]
    for arm in ARMS:
        require(cumulative_input[arm][-1] == stored["final_input_tokens"][arm],
                f"arm final input mismatch: {arm}")
        require(report_eval["arms"][arm]["cumulative_input_tokens"] == cumulative_input[arm],
                f"task cumulative input mismatch: {arm}")
        require(report_eval["arms"][arm]["cumulative_planner_generations"] == cumulative_generations[arm],
                f"task generation mismatch: {arm}; recomputed={cumulative_generations[arm]} reported={report_eval['arms'][arm]['cumulative_planner_generations']}")
    persistent = cumulative_input["persistent"][-1]
    require(persistent < cumulative_input["plain"][-1]
            and persistent < cumulative_input["ephemeral"][-1], "token threshold fails")
    require(cumulative_generations["persistent"][-1] < cumulative_generations["plain"][-1]
            and cumulative_generations["persistent"][-1] < cumulative_generations["ephemeral"][-1],
            "generation threshold fails")
    break_even = next((i for i in range(6)
                       if cumulative_input["persistent"][i] < cumulative_input["plain"][i]
                       and cumulative_input["persistent"][i] < cumulative_input["ephemeral"][i]), None)
    require(break_even == 1, f"unexpected first break-even index: {break_even}")
    repair = trace["arms"]["persistent"][3]["repair"]
    require(repair["required"] and repair["old_reference_status"] == "missing"
            and repair["old_reference_pointer_admissions"] == 0
            and repair["attempted"] and repair["succeeded"], "task-4 repair mismatch")
    require(all(t["old_target_pointer_admissions"] == 0
                for arm in ARMS for t in trace["arms"][arm]), "stale pointer admission present")

    result = {
        "schema": "integrated-efficiency-live-independent-recount-v1",
        "status": "PASS_SCOPED_EVIDENCE_RECOUNT",
        "scope": freeze["scope"],
        "source_main_commit": freeze["source_main_commit"],
        "inputs": {name: sha(path) for name, path in files.items()},
        "raw_image_result_files": len(raw_calls), "fresh_preflight_calls": 3,
        "globally_unique_image_call_ids": len(image_ids),
        "task_rows": task_counts, "exact_history_submissions": submission_counts,
        "usage_totals": totals, "final_input_tokens": {a: cumulative_input[a][-1] for a in ARMS},
        "cumulative_input_tokens": cumulative_input,
        "cumulative_planner_generations": cumulative_generations,
        "first_break_even_task": break_even + 1,
        "persistent_task4_repair": repair,
        "reported_disposition_thresholds": "PASS_SCOPED",
        "independent_of_existing_audit_code": True,
        "errors": []
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"status": "FAIL_AUDIT", "error": str(exc)}), file=sys.stderr)
        raise
