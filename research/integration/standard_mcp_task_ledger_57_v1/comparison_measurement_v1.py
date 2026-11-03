"""Lifecycle/image accounting validator for a matched Issue #57 task block.

The underlying standard task ledger remains the authority for attempts, tool
calls, token usage and independent score. This envelope adds explicit elapsed
time, contiguous phase coverage, model-delivered images and local observations.
It validates supplied evidence metadata; it cannot prove that instrumentation
captured every external event.
"""

from __future__ import annotations

import re

from ledger import LedgerValidationError, validate_record


_HASH = re.compile(r"^[0-9a-f]{64}$")
_ARMS = {"A", "B", "C"}
_PHASES = {
    "setup_acquisition", "observation_grounding", "provider_wait",
    "plan_validation", "local_execution", "effect_verification",
    "cleanup", "recovery", "other",
}
_OBSERVATION_METHODS = {
    "interface_guarded_observe", "interface_guarded_review_window",
    "interface_guarded_feedback",
}


def _integer(value):
    return type(value) is int and value >= 0


def _fail(message):
    raise LedgerValidationError(message)


def validate_measured_run(value):
    """Validate one standard ledger plus complete lifecycle measurement."""
    if type(value) is not dict or set(value) != {"task_ledger", "measurement"}:
        _fail("measured run requires exactly task_ledger and measurement")
    record = value["task_ledger"]
    summary = validate_record(record)
    measurement = value["measurement"]
    if type(measurement) is not dict or set(measurement) != {
            "started_ns", "ended_ns", "elapsed_ns", "phases",
            "model_delivered_images", "local_observations"}:
        _fail("measurement fields do not match the lifecycle schema")

    started, ended = measurement["started_ns"], measurement["ended_ns"]
    elapsed = measurement["elapsed_ns"]
    if (not _integer(started) or not _integer(ended) or ended <= started
            or not _integer(elapsed) or elapsed != ended - started):
        _fail("measurement needs a consistent positive full-lifecycle interval")

    phases = measurement["phases"]
    if type(phases) is not list or not phases:
        _fail("measurement needs a phase sequence covering the full lifecycle")
    cursor = started
    phase_totals = {}
    for phase in phases:
        if type(phase) is not dict or set(phase) - {
                "name", "started_ns", "ended_ns", "reason"}:
            _fail("phase has unknown fields")
        name, pstart, pend = (phase.get("name"), phase.get("started_ns"),
                              phase.get("ended_ns"))
        if name not in _PHASES or not _integer(pstart) or not _integer(pend):
            _fail("phase name or monotonic interval is invalid")
        if pstart != cursor or pend <= pstart or pend > ended:
            _fail("phases must be ordered, contiguous and inside the lifecycle")
        if name == "other" and (not isinstance(phase.get("reason"), str)
                                or not phase["reason"].strip()):
            _fail("other phase needs an explicit reason")
        if name != "other" and "reason" in phase:
            _fail("reason is only valid for an other phase")
        phase_totals[name] = phase_totals.get(name, 0) + pend - pstart
        cursor = pend
    if cursor != ended:
        _fail("phase sequence does not cover lifecycle end")

    events = record["events"]
    for event in events:
        if event["started_ns"] < started or event["ended_ns"] > ended:
            _fail("ledger event falls outside the full-lifecycle interval")

    raw_hashes = {reference["sha256"] for reference in record["raw_refs"]}
    attempts = {event["attempt_id"] for event in events
                if event["kind"] == "model_attempt"}
    calls = {event["call_id"]: event for event in events
             if event["kind"] == "tool_call"}

    model_images = measurement["model_delivered_images"]
    if type(model_images) is not list:
        _fail("model-delivered images must be an explicit list")
    for image in model_images:
        if type(image) is not dict or set(image) != {"attempt_id", "sha256"}:
            _fail("model image needs attempt_id and sha256")
        if image["attempt_id"] not in attempts or not isinstance(
                image["sha256"], str) or not _HASH.fullmatch(image["sha256"]):
            _fail("model image must bind to a recorded attempt and digest")
        if image["sha256"] not in raw_hashes:
            _fail("model image digest is not retained in raw evidence")

    observations = measurement["local_observations"]
    if type(observations) is not list:
        _fail("local observations must be an explicit list")
    observation_ids = set()
    for observation in observations:
        if type(observation) is not dict or set(observation) != {
                "tool_call_id", "source_sequence", "captured_ns", "image_sha256"}:
            _fail("local observation fields do not match the schema")
        call_id = observation["tool_call_id"]
        event = calls.get(call_id)
        if event is None or event["method"] not in _OBSERVATION_METHODS:
            _fail("local observation must link to a recorded observation tool call")
        if call_id in observation_ids:
            _fail("local observation tool call is duplicated")
        observation_ids.add(call_id)
        if not _integer(observation["source_sequence"]) or observation[
                "source_sequence"] <= 0:
            _fail("observation source sequence must be positive")
        if not _integer(observation["captured_ns"]) or not (
                event["started_ns"] <= observation["captured_ns"] <= event["ended_ns"]):
            _fail("capture time must fall within its observation tool call")
        digest = observation["image_sha256"]
        if not isinstance(digest, str) or not _HASH.fullmatch(digest) or digest not in raw_hashes:
            _fail("local observation image must be retained by digest")
        result_source = event["result"].get("source")
        if (not isinstance(result_source, dict)
                or result_source.get("sequence") != observation["source_sequence"]):
            _fail("observation sequence does not match the public tool receipt")

    return {
        **summary,
        "elapsed_ns": elapsed,
        "phase_durations_ns": phase_totals,
        "model_delivered_image_count": len(model_images),
        "local_observation_count": len(observations),
    }


def validate_matched_block(runs):
    """Validate one A/B/C block with identical task/model/environment pins."""
    if type(runs) is not list or len(runs) != 3:
        _fail("one matched block requires exactly three measured runs")
    measured = [validate_measured_run(run) for run in runs]
    records = [run["task_ledger"] for run in runs]
    arms = [record["comparison"]["arm"] for record in records]
    if set(arms) != _ARMS or len(set(arms)) != 3:
        _fail("matched block must contain exactly arms A, B and C")
    blocks = {record["comparison"]["block"] for record in records}
    if len(blocks) != 1:
        _fail("runs do not share one comparison block")
    orders = [record["comparison"]["order"] for record in records]
    if set(orders) != {1, 2, 3}:
        _fail("matched run order must be a permutation of 1, 2 and 3")

    first = records[0]
    for record in records[1:]:
        if record["comparison"]["task_seed"] != first["comparison"]["task_seed"]:
            _fail("matched arms must use the same task seed")
        if (record["task"]["task_id"], record["task"]["fixture_sha256"],
                record["task"]["scorer_sha256"]) != (
                first["task"]["task_id"], first["task"]["fixture_sha256"],
                first["task"]["scorer_sha256"]):
            _fail("matched arms must pin the same task fixture and scorer")
        if record["model"] != first["model"]:
            _fail("matched arms must use the same model and request settings")
        if record["environment_sha256"] != first["environment_sha256"]:
            _fail("matched arms must pin the same environment")

    return {
        "block": next(iter(blocks)),
        "task_id": first["task"]["task_id"],
        "arms": {record["comparison"]["arm"]: result
                 for record, result in zip(records, measured)},
    }


def validate_reuse_horizon(value):
    """Validate cold/warm/one-repair/post-repair reuse and cumulative outcomes.

    The horizon is a predeclared sequence of matched A/B/C task blocks. Arm C
    has one semantic-plan lineage: a cold generation, one or more warm uses,
    exactly one staged dependency change and repair, then post-repair warm use.
    Token counts and elapsed time are accumulated separately.
    """
    if type(value) is not dict or set(value) != {
            "schema", "comparison_id", "predeclared_horizon",
            "invalidation_after_task_index", "blocks", "c_plan_trace"}:
        _fail("reuse horizon fields do not match the comparison schema")
    if value["schema"] != "agent-interface/reuse-horizon-comparison-v1":
        _fail("unsupported reuse-horizon schema")
    if not isinstance(value["comparison_id"], str) or not value["comparison_id"].strip():
        _fail("comparison_id is required")
    horizon = value["predeclared_horizon"]
    blocks = value["blocks"]
    if (type(horizon) is not int or horizon < 4 or type(blocks) is not list
            or len(blocks) != horizon):
        _fail("observed blocks must equal a predeclared horizon of at least four tasks")
    invalidation_after = value["invalidation_after_task_index"]
    if type(invalidation_after) is not int or not 2 <= invalidation_after < horizon:
        _fail("invalidation position must follow cold plus warm use and precede repair")

    validated_blocks = []
    model_pin = environment_pin = fixture_pin = scorer_pin = None
    route_pins = {}
    task_ids = set()
    task_seeds = set()
    for index, block in enumerate(blocks, start=1):
        if type(block) is not dict or set(block) != {
                "task_index", "predeclared_order", "runs"}:
            _fail("each horizon block needs task_index, predeclared_order and runs")
        if block["task_index"] != index:
            _fail("horizon task indices must be contiguous and ordered")
        summary = validate_matched_block(block["runs"])
        records = [run["task_ledger"] for run in block["runs"]]
        declared_order = block["predeclared_order"]
        actual_order = [record["comparison"]["arm"] for record in sorted(
            records, key=lambda item: item["comparison"]["order"])]
        if (type(declared_order) is not list or len(declared_order) != 3
                or set(declared_order) != _ARMS or declared_order != actual_order):
            _fail("observed arm order must match the preregistered block order")
        if summary["block"] != index:
            _fail("matched block number must equal its horizon index")
        task_id = records[0]["task"]["task_id"]
        if task_id in task_ids:
            _fail("each horizon task needs a distinct task_id")
        task_ids.add(task_id)
        task_seed = records[0]["comparison"]["task_seed"]
        if task_seed in task_seeds:
            _fail("each horizon task needs a distinct preregistered seed")
        task_seeds.add(task_seed)
        if records[0]["model"] is None:
            _fail("reuse horizon requires a pinned model condition")
        for record in records:
            if model_pin is None:
                model_pin = record["model"]
                environment_pin = record["environment_sha256"]
                fixture_pin = record["task"]["fixture_sha256"]
                scorer_pin = record["task"]["scorer_sha256"]
            if (record["model"] != model_pin
                    or record["environment_sha256"] != environment_pin
                    or record["task"]["fixture_sha256"] != fixture_pin
                    or record["task"]["scorer_sha256"] != scorer_pin):
                _fail("reuse horizon must keep model, environment, task fixture and scorer fixed")
            arm = record["comparison"]["arm"]
            route = record["source"]["route_sha256"]
            if arm in route_pins and route_pins[arm] != route:
                _fail("each comparison arm must keep its route source fixed over the horizon")
            route_pins[arm] = route
        validated_blocks.append(summary)

    trace = value["c_plan_trace"]
    if type(trace) is not list or len(trace) != horizon:
        _fail("C plan trace must contain one entry per horizon task")
    c_attempts = []
    for block in blocks:
        run_c = next(run for run in block["runs"]
                     if run["task_ledger"]["comparison"]["arm"] == "C")
        c_attempts.append({event["attempt_id"] for event in
                           run_c["task_ledger"]["events"]
                           if event["kind"] == "model_attempt"})

    normalized_trace = []
    plan_digest = dependency_digest = repair_plan = repair_dependency = None
    repair_index = invalidation_after + 1
    for index, row in enumerate(trace, start=1):
        required = {"task_index", "mode", "plan_sha256", "source_task_index",
                    "dependency_sha256", "plan_generation_attempt_ids"}
        if type(row) is not dict or set(row) != required or row["task_index"] != index:
            _fail("C plan trace fields and order are invalid")
        mode = row["mode"]
        if row["plan_sha256"] is None:
            _fail("each C task needs a retained semantic-plan digest")
        if not isinstance(row["plan_sha256"], str) or not _HASH.fullmatch(row["plan_sha256"]):
            _fail("plan digest must be lowercase SHA-256")
        if not isinstance(row["dependency_sha256"], str) or not _HASH.fullmatch(
                row["dependency_sha256"]):
            _fail("dependency digest must be lowercase SHA-256")
        attempt_ids = row["plan_generation_attempt_ids"]
        if (type(attempt_ids) is not list or len(attempt_ids) != len(set(attempt_ids))
                or any(not isinstance(item, str) or not item for item in attempt_ids)):
            _fail("plan generation attempts must be a unique explicit list")
        if any(attempt not in c_attempts[index - 1] for attempt in attempt_ids):
            _fail("plan generation attempt is absent from the matching C ledger")
        if set(attempt_ids) != c_attempts[index - 1]:
            _fail("every C model attempt must be accounted as plan generation in this horizon")

        if index == 1:
            if mode != "cold" or row["source_task_index"] is not None or not attempt_ids:
                _fail("first C task must cold-generate its plan from a recorded attempt")
            if validated_blocks[index - 1]["arms"]["C"]["task_success"] is not True:
                _fail("cold C plan task must pass its independent task score")
            plan_digest = row["plan_sha256"]
            dependency_digest = row["dependency_sha256"]
        elif index < repair_index:
            if (mode != "warm" or row["source_task_index"] != 1 or attempt_ids
                    or row["plan_sha256"] != plan_digest
                    or row["dependency_sha256"] != dependency_digest):
                _fail("pre-invalidation C tasks must reuse the cold plan without regeneration")
        elif index == repair_index:
            if (mode != "repair" or row["source_task_index"] != index or not attempt_ids
                    or row["plan_sha256"] == plan_digest
                    or row["dependency_sha256"] == dependency_digest):
                _fail("declared invalidation must cause exactly one fresh plan repair")
            if validated_blocks[index - 1]["arms"]["C"]["task_success"] is not True:
                _fail("repaired C plan task must pass its independent task score")
            repair_plan = row["plan_sha256"]
            repair_dependency = row["dependency_sha256"]
        else:
            if (mode != "post_repair_warm" or row["source_task_index"] != repair_index
                    or attempt_ids or row["plan_sha256"] != repair_plan
                    or row["dependency_sha256"] != repair_dependency):
                _fail("post-repair tasks must reuse the repaired plan without regeneration")
        normalized_trace.append(dict(row))

    cumulative = {arm: {"input_tokens": [], "output_tokens": [],
                        "total_tokens": [], "elapsed_ns": [],
                        "task_success": [], "model_delivered_image_count": [],
                        "local_observation_count": []}
                  for arm in sorted(_ARMS)}
    running = {arm: {"input_tokens": 0, "output_tokens": 0,
                     "elapsed_ns": 0, "model_delivered_image_count": 0,
                     "local_observation_count": 0, "usage_complete": True}
               for arm in _ARMS}
    break_even = {baseline: None for baseline in ("A", "B")}
    qualified_break_even = {baseline: None for baseline in ("A", "B")}
    elapsed_break_even = {baseline: None for baseline in ("A", "B")}
    qualified_elapsed_break_even = {baseline: None for baseline in ("A", "B")}
    all_correct_so_far = True

    for index, block in enumerate(validated_blocks, start=1):
        for arm in _ARMS:
            current = block["arms"][arm]
            state = running[arm]
            if current["input_tokens"] is None or current["output_tokens"] is None:
                state["usage_complete"] = False
            if state["usage_complete"]:
                state["input_tokens"] += current["input_tokens"]
                state["output_tokens"] += current["output_tokens"]
            state["elapsed_ns"] += current["elapsed_ns"]
            state["model_delivered_image_count"] += current[
                "model_delivered_image_count"]
            state["local_observation_count"] += current["local_observation_count"]
            cumulative[arm]["input_tokens"].append(
                state["input_tokens"] if state["usage_complete"] else None)
            cumulative[arm]["output_tokens"].append(
                state["output_tokens"] if state["usage_complete"] else None)
            cumulative[arm]["total_tokens"].append(
                state["input_tokens"] + state["output_tokens"]
                if state["usage_complete"] else None)
            cumulative[arm]["elapsed_ns"].append(state["elapsed_ns"])
            cumulative[arm]["task_success"].append(current["task_success"])
            cumulative[arm]["model_delivered_image_count"].append(
                state["model_delivered_image_count"])
            cumulative[arm]["local_observation_count"].append(
                state["local_observation_count"])

        all_correct_so_far = all_correct_so_far and all(
            block["arms"][arm]["task_success"] is True for arm in _ARMS)
        c_total = cumulative["C"]["total_tokens"][-1]
        for baseline in ("A", "B"):
            base_total = cumulative[baseline]["total_tokens"][-1]
            if (break_even[baseline] is None and c_total is not None
                    and base_total is not None and c_total < base_total):
                break_even[baseline] = index
            if (qualified_break_even[baseline] is None and all_correct_so_far
                    and c_total is not None and base_total is not None
                    and c_total < base_total):
                qualified_break_even[baseline] = index
            c_elapsed = cumulative["C"]["elapsed_ns"][-1]
            base_elapsed = cumulative[baseline]["elapsed_ns"][-1]
            if (elapsed_break_even[baseline] is None
                    and c_elapsed < base_elapsed):
                elapsed_break_even[baseline] = index
            if (qualified_elapsed_break_even[baseline] is None
                    and all_correct_so_far and c_elapsed < base_elapsed):
                qualified_elapsed_break_even[baseline] = index

    return {
        "comparison_id": value["comparison_id"],
        "predeclared_horizon": horizon,
        "invalidation_after_task_index": invalidation_after,
        "plan_trace": normalized_trace,
        "cumulative": cumulative,
        "token_break_even_task_index": break_even,
        "correctness_qualified_token_break_even_task_index": qualified_break_even,
        "elapsed_break_even_task_index": elapsed_break_even,
        "correctness_qualified_elapsed_break_even_task_index": qualified_elapsed_break_even,
        "break_even_scope": "reported input+output tokens and full lifecycle elapsed time have separate strict break-even indices; cached/reasoning are token detail metrics",
    }
