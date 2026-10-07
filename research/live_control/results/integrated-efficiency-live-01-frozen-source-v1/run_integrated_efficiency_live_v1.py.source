"""Run the preregistered six-task, three-arm integrated efficiency allocation."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from adaptive_acquisition_caller_v2 import run as run_adaptive
from integrated_efficiency_client_v1 import RuntimeClient
from integrated_efficiency_model_v1 import CONTRACTS, call as call_model
from integrated_efficiency_protocol_v1 import ARMS, evaluate
from schema_preflight_gate_v1 import require_compatible


HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "integrated-efficiency-live-01"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")


def records(path):
    path = Path(path)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def preflight_call(arm, contract):
    root = OUT / "preflight" / arm
    workspace = OUT / "workspaces" / arm
    workspace.mkdir(parents=True, exist_ok=False)
    schema = CONTRACTS[contract][0]
    gate = require_compatible(
        [{"name": contract + "-form-grounding", "schema": schema}],
        root / "fresh-cache", root / "gate", workspace)
    result = gate["results"][0]["result"]
    events = records(root / "gate" / (contract + "-form-grounding") /
                     "model-call" / "events.jsonl")
    threads = [row["thread_id"] for row in events if row.get("type") == "thread.started"]
    if (gate["accepted"] is not True or result["model_call_performed"] is not True
            or result["cache_hit"] is not False or result["usage"] is None
            or len(threads) != 1):
        raise RuntimeError("fresh schema preflight was not fully observed for " + arm)
    return {"call_id": threads[0], "stage": "schema_preflight",
            "requested_model": result["identity"]["requested_model"],
            "requested_effort": result["identity"]["requested_effort"],
            "usage": result["usage"], "model_visible_images": 0}


def feedback_times(programs):
    observations = sorted(
        (row["capture_ns"] for program in programs for row in program["observations"]),
    )
    downs = [row["input_ack_ns"] for program in programs
             for row in program["pointer_admissions"]
             if row.get("operation") == "button_down"]
    return [next((capture - ack for capture in observations if capture >= ack), None)
            for ack in downs]


def model_record(row):
    return {"call_id": row["call_id"], "stage": row["stage"],
            "requested_model": row["requested_model"],
            "requested_effort": row["requested_effort"], "usage": row["usage"]}


def run_task(client, arm, task, index, cached, workspace, model_root):
    task_started = time.perf_counter_ns()
    program_start = len(client.programs)
    durable_start = client.durable_calls
    history_path = client.runtime / "submission-history.jsonl"
    history_start = len(records(history_path))
    source = client.navigate(task)
    current_source = source
    resolved = None
    invalidation = None
    contract = "plain" if arm == "plain" else "compiled"
    scheduled_route = ("cold" if arm != "persistent" or index == 0 else "reuse")

    def grounding(stage):
        result = call_model(model_root / task["task_id"] / stage,
            "Locate the editable token field and the control that submits this visible form. ",
            Path(current_source["image"]), contract, workspace)
        target = {"grounding": result["grounding"], "aliases": None,
                  "needs_mint": arm != "plain", "layout": task["layout"]}
        return {"call_id": result["call_id"],
                "output": {"status": "target_reference", "target": target},
                "usage": result["usage"], "requested_model": result["requested_model"],
                "requested_effort": result["requested_effort"], "cost": result["cost"]}

    def reuse_revalidate(target):
        nonlocal invalidation, resolved
        resolved = target
        checks = []
        for kind, offset in (("field", [12, 19]), ("submit", [12, 7])):
            check, program = client.check(target["aliases"][kind], offset,
                "reuse-" + kind + "-" + task["task_id"])
            checks.append(check)
            if not check["eligible"]:
                invalidation = {"status": check["status"].lower(),
                    "old_reference_pointer_admissions": sum(
                        row.get("operation") == "button_down"
                        for row in program["pointer_admissions"])}
                return {"status": ("no_match" if check["status"] == "MISSING"
                                   else check["status"].lower())}
        return {"status": "revalidated", "checks": checks}

    def final_revalidate(target):
        nonlocal resolved
        resolved = target
        if target["needs_mint"]:
            prefix = (f"{arm}_{task['task_id']}_{task['layout'].lower()}"
                      if arm == "ephemeral" else
                      f"persistent_{task['layout'].lower()}")
            aliases, refusal = client.mint(task["layout"], current_source,
                                            target["grounding"], prefix)
            if refusal is not None:
                return {"status": "unavailable"}
            resolved = {**target, "aliases": aliases, "needs_mint": False}
        elif arm != "plain":
            for kind, offset in (("field", [12, 19]), ("submit", [12, 7])):
                check, _program = client.check(resolved["aliases"][kind], offset,
                    "final-" + kind + "-" + task["task_id"])
                if not check["eligible"]:
                    return {"status": ("no_match" if check["status"] == "MISSING"
                                       else check["status"].lower())}
        return {"status": "revalidated"}

    def execute(_payload):
        result = (client.execute_plain(task, resolved["grounding"])
                  if arm == "plain" else client.execute_handles(task, resolved["aliases"]))
        if result["status"] == "completed":
            return {"status": "completed"}
        if result["status"] == "safe_yield":
            return {key: result[key] for key in ("status", "reason", "completed_actions")}
        return {"status": "failed"}

    def verify(_payload):
        visible = any("AI INTEGRATED SAVED" in str(observation.get("context", ""))
                      for program in client.programs[program_start:]
                      for observation in program["observations"])
        return {"status": "succeeded" if visible else "failed"}

    spec = {"target": "submit the exact task token", "route": scheduled_route,
            "coarse_origin": "caller_provided",
            "provided_coarse": ({"source_sequence": source["sequence"]}
                                if scheduled_route == "cold" else None),
            "cached_target": cached if scheduled_route == "reuse" else None,
            "repair_on": ["no_match"] if arm == "persistent" else [],
            "session_id": arm}
    adaptive = run_adaptive(spec, {
        "observe_source": lambda _payload: {"source_sequence": source["sequence"]},
        "acquire_anchor": lambda _payload: {"source": source},
        "anchor_model": lambda _payload: grounding("anchor"),
        "reuse_revalidate": reuse_revalidate,
        "acquire_expansion": lambda _payload: {"source": source},
        "expanded_model": lambda _payload: grounding("repair"),
        "final_revalidate": final_revalidate, "execute": execute,
        "verify_effect": verify}, id_factory=lambda: arm + ":" + task["task_id"])
    task_ended = time.perf_counter_ns()
    programs = client.programs[program_start:]
    new_history = records(history_path)[history_start:]
    matching = [row for row in new_history if row.get("task_id") == task["task_id"]]
    exact = len(matching) == 1 and matching[0].get("exact") is True
    completion_ns = matching[0]["received_ns"] if len(matching) == 1 else None
    repair_required = arm == "persistent" and index == 3
    calls = [model_record(row) for row in adaptive["model_call_ledger"]]
    route = "repair" if repair_required else scheduled_route
    pointer_admissions = sum(event.get("operation") == "button_down"
                             for program in programs for event in program["pointer_admissions"])
    releases = [program["terminal"]["release"] for program in programs]
    row = {"arm": arm, "task_id": task["task_id"], "layout": task["layout"],
        "route": route, "model_calls": calls, "planner_generations": len(calls),
        "model_visible_images": len(calls),
        "local_observations": sum(len(program["observations"]) for program in programs),
        "durable_calls": client.durable_calls - durable_start,
        "pointer_admissions": pointer_admissions,
        "old_target_pointer_admissions": (0 if invalidation is None else
                                           invalidation["old_reference_pointer_admissions"]),
        "releases_verified": bool(releases) and all(release["verified"] is True
            and release["keys_down"] == [] and release["buttons_down"] == []
            for release in releases),
        "submission_count": len(matching), "exact_submission": exact,
        "typed_outcome": ("completed" if adaptive["outcome"] == "TASK_SUCCEEDED"
                          else "safe_stop" if adaptive["outcome"] == "SAFE_STOP" else "failed"),
        "elapsed_ns": task_ended - task_started,
        "source_to_completion_ns": (None if completion_ns is None else
                                     completion_ns - source["capture_ns"]),
        "input_feedback_ns": feedback_times(programs),
        "repair": ({"required": True,
            "old_reference_status": None if invalidation is None else invalidation["status"],
            "old_reference_pointer_admissions": (0 if invalidation is None else
                invalidation["old_reference_pointer_admissions"]),
            "attempted": bool(calls), "succeeded": adaptive["outcome"] == "TASK_SUCCEEDED"}
            if repair_required else {"required": False, "old_reference_status": None,
                "old_reference_pointer_admissions": 0, "attempted": False,
                "succeeded": False})}
    detail = {"trace": row, "source": source, "adaptive": adaptive,
              "program_count": len(programs), "submission_records": new_history,
              "resolved_target": resolved}
    return row, resolved if adaptive["outcome"] == "TASK_SUCCEEDED" else cached, detail


def run_arm(arm, seed, workspace):
    rows, details, cached = [], [], None
    with RuntimeClient(OUT / "arms" / arm, seed) as client:
        for index, task in enumerate(client.ready["goal"]["tasks"]):
            row, cached, detail = run_task(client, arm, task, index, cached,
                                            workspace, OUT / "model-calls" / arm)
            rows.append(row); details.append(detail)
        independent = client.finish("finish-integrated-live-01-" + arm)
        final_history = records(client.runtime / "submission-history.jsonl")
        for row, detail in zip(rows, details):
            matching = [record for record in final_history
                        if record.get("task_id") == row["task_id"]]
            row["submission_count"] = len(matching)
            row["exact_submission"] = (len(matching) == 1
                                       and matching[0].get("exact") is True)
            row["source_to_completion_ns"] = (None if len(matching) != 1 else
                matching[0]["received_ns"] - detail["source"]["capture_ns"])
            detail["submission_records"] = matching
    dump(OUT / "arms" / arm / "task-details.json", details)
    return rows, independent


def main():
    plan = json.loads((OUT / "preregistration.json").read_text(encoding="utf-8"))
    for name, digest in plan["sources"].items():
        if sha(HERE / name) != digest:
            raise RuntimeError("source changed after preregistration: " + name)
    preflights = {}
    for arm in ARMS:
        preflights[arm] = preflight_call(arm, "plain" if arm == "plain" else "compiled")
    arms, independent = {}, {}
    for arm in ARMS:
        arms[arm], independent[arm] = run_arm(
            arm, plan["seed"], OUT / "workspaces" / arm)
    trace = {"schema": "integrated_efficiency_trace_v1", "arms": arms,
             "preflight_calls": preflights,
             "integration_discoveries": json.loads(
                 (HERE / "integrated_efficiency_discoveries_v1.json").read_text(encoding="utf-8"))}
    dump(OUT / "trace.json", trace)
    evaluation = evaluate(trace)
    report = {"schema": "integrated_efficiency_live_report_v1",
              "evaluation": evaluation, "independent_evaluations": independent,
              "preflight_calls": preflights, "scope": plan["scope"]}
    dump(OUT / "report.json", report)
    print(json.dumps({"disposition": evaluation["disposition"],
                      "break_even": evaluation["observed_break_even_task"],
                      "correct": {arm: evaluation["arms"][arm]["correct"] for arm in ARMS},
                      "tokens": {arm: evaluation["arms"][arm]["cumulative_input_tokens"][-1]
                                 for arm in ARMS}}, indent=2))


if __name__ == "__main__":
    main()
