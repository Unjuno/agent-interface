"""Shared acquisition caller with local-first semantic repair.

Version 3 preserves the v2 typed execution and all-attempt accounting boundary.
For warm reuse it can try one no-authority local repair before model
reacquisition.  Every repair model result must be checked against one later
observation before ordinary final revalidation and execution.
"""
import copy
import time
import uuid


USAGE_FIELDS = ("input_tokens", "cached_input_tokens",
                "cache_write_input_tokens", "output_tokens",
                "reasoning_output_tokens")
MODEL_STAGES = ("coarse_model", "anchor_model", "expanded_model")
ALL_STAGES = ("observe_source", "coarse_model", "acquire_anchor",
              "anchor_model", "reuse_revalidate", "local_repair",
              "acquire_expansion", "expanded_model", "post_model_observe",
              "post_model_revalidate", "final_revalidate", "execute",
              "verify_effect")
STOP_REASONS = {"no_match", "search_exhausted", "ambiguous",
                "unavailable", "stale", "association_changed", "missing"}
LOCAL_EXECUTION_YIELD_REASONS = {
    "unknown_state", "ambiguous_state", "stale_observation", "stale_symbol",
    "missing_symbol", "association_changed", "authority_unavailable",
    "effect_failed", "effect_unavailable", "no_progress", "cancelled",
    "budget_exhausted", "delivery_uncertain", "execution_failed",
}


class ModelFailure(RuntimeError):
    def __init__(self, message, *, call_id=None, usage=None,
                 visible_images_submitted=None, wait_ns=None,
                 typed_status="FAILED_UPSTREAM"):
        super().__init__(message)
        if typed_status not in {"DEFERRED_UPSTREAM", "FAILED_UPSTREAM",
                                "FAILED_OUTPUT"}:
            raise ValueError("known typed model failure status required")
        self.call_id = call_id
        self.usage = usage
        self.visible_images_submitted = visible_images_submitted
        self.wait_ns = wait_ns
        self.typed_status = typed_status


def _require_callable(adapters, name):
    value = adapters.get(name)
    if not callable(value):
        raise ValueError(f"callable adapter required for {name}")
    return value


def _usage(value):
    if value is None:
        return None
    if type(value) is not dict:
        raise ValueError("usage must be an object or unavailable")
    unknown = set(value) - set(USAGE_FIELDS)
    if unknown:
        raise ValueError("unknown usage fields: " + ",".join(sorted(unknown)))
    for key, amount in value.items():
        if type(amount) is not int or amount < 0:
            raise ValueError(f"nonnegative integer usage required for {key}")
    return copy.deepcopy(value)


def _optional_count(value, name):
    if value is not None and (type(value) is not int or value < 0):
        raise ValueError(f"nonnegative integer or unavailable required for {name}")
    return value


def _model_result(value):
    required = {"call_id", "output", "usage", "requested_model",
                "requested_effort", "cost", "visible_images_submitted",
                "wait_ns"}
    if type(value) is not dict or set(value) != required:
        raise ValueError("exact v3 model result fields required")
    if type(value["call_id"]) is not str or not value["call_id"]:
        raise ValueError("nonempty model call id required")
    if type(value["requested_model"]) is not str or not value["requested_model"]:
        raise ValueError("requested model identity required")
    if type(value["requested_effort"]) is not str or not value["requested_effort"]:
        raise ValueError("requested effort required")
    if value["cost"] is not None and not isinstance(value["cost"], (int, float)):
        raise ValueError("cost must be numeric or unavailable")
    result = copy.deepcopy(value)
    result["usage"] = _usage(value["usage"])
    result["visible_images_submitted"] = _optional_count(
        value["visible_images_submitted"], "visible_images_submitted")
    result["wait_ns"] = _optional_count(value["wait_ns"], "wait_ns")
    return result


def _decision(value, allowed):
    if type(value) is not dict or type(value.get("status")) is not str:
        raise ValueError("typed decision object required")
    if value["status"] not in allowed:
        raise ValueError("unsupported decision status " + value["status"])
    if value["status"] in STOP_REASONS and value.get("target") is not None:
        raise ValueError("stop decision must not expose a target")
    return copy.deepcopy(value)


def _local_repair_decision(value):
    if type(value) is not dict or value.get("status") not in ({"repaired"} | STOP_REASONS):
        raise ValueError("typed local repair decision required")
    if value["status"] != "repaired":
        if value.get("target") is not None:
            raise ValueError("failed local repair must not expose a target")
        return copy.deepcopy(value)
    required = {"status", "target", "receipt", "model_calls",
                "grants_semantic_authority", "grants_input_authority"}
    if set(value) != required or value["target"] is None or \
            type(value["receipt"]) is not dict or value["model_calls"] != 0 or \
            value["grants_semantic_authority"] is not False or \
            value["grants_input_authority"] is not False:
        raise ValueError("exact no-authority local repair required")
    return copy.deepcopy(value)


def _post_model_decision(value, call_id, current_observation):
    if type(value) is not dict or value.get("status") not in \
            ({"current_patch_match"} | STOP_REASONS):
        raise ValueError("typed post-model revalidation required")
    if value["status"] != "current_patch_match":
        if value.get("target") is not None:
            raise ValueError("failed post-model check must not expose a target")
        return copy.deepcopy(value)
    required = {"status", "target", "receipt", "model_call_id",
                "grants_semantic_authority", "grants_input_authority"}
    receipt = value.get("receipt")
    if type(current_observation) is not dict or \
            current_observation.get("exact") is not True or \
            type(current_observation.get("sequence")) is not int or \
            type(current_observation.get("capture_ns")) is not int or \
            type(current_observation.get("pointer_binding")) is not dict:
        raise ValueError("exact current observation required after model return")
    if set(value) != required or value["target"] is None or \
            type(receipt) is not dict or value["model_call_id"] != call_id or \
            receipt.get("schema") != "post-model-target-revalidation-v1" or \
            receipt.get("status") != "CURRENT_PATCH_MATCH_NO_AUTHORITY" or \
            receipt.get("model_call_id") != call_id or \
            receipt.get("current_sequence", 0) <= receipt.get("model_source_sequence", 0) or \
            receipt.get("current_sequence") != current_observation["sequence"] or \
            receipt.get("current_capture_ns") != current_observation["capture_ns"] or \
            receipt.get("pointer_binding") != current_observation["pointer_binding"] or \
            receipt.get("grants_semantic_authority") is not False or \
            receipt.get("grants_input_authority") is not False or \
            value["grants_semantic_authority"] is not False or \
            value["grants_input_authority"] is not False:
        raise ValueError("exact current no-authority model target check required")
    return copy.deepcopy(value)


def _execution_decision(value):
    if type(value) is not dict or type(value.get("status")) is not str:
        raise ValueError("typed execution decision object required")
    status = value["status"]
    if status in {"completed", "delivery_uncertain", "failed"}:
        if set(value) != {"status"}:
            raise ValueError("legacy execution decision accepts status only")
        return copy.deepcopy(value)
    if status != "safe_yield" or set(value) != {"status", "reason", "completed_actions"}:
        raise ValueError("exact safe_yield execution decision required")
    if value["reason"] not in LOCAL_EXECUTION_YIELD_REASONS:
        raise ValueError("unsupported local execution yield reason " + str(value["reason"]))
    if type(value["completed_actions"]) is not int or value["completed_actions"] < 0:
        raise ValueError("nonnegative completed_actions required")
    return copy.deepcopy(value)


def _validate_spec(spec):
    required = {"target", "route", "coarse_origin", "provided_coarse",
                "cached_target", "local_repair_on", "repair_on", "session_id"}
    if type(spec) is not dict or set(spec) != required:
        raise ValueError("exact adaptive caller v3 specification required")
    if type(spec["target"]) is not str or not spec["target"]:
        raise ValueError("nonempty target required")
    if spec["route"] not in ("cold", "reuse"):
        raise ValueError("route must be cold or reuse")
    if spec["coarse_origin"] not in ("model_produced", "caller_provided", "injected_archive"):
        raise ValueError("declared coarse origin required")
    for field in ("local_repair_on", "repair_on"):
        if type(spec[field]) is not list or any(v not in STOP_REASONS for v in spec[field]):
            raise ValueError(field + " must contain typed stop reasons")
        if len(spec[field]) != len(set(spec[field])):
            raise ValueError(field + " must not contain duplicates")
    if type(spec["session_id"]) is not str or not spec["session_id"]:
        raise ValueError("session id required")
    if spec["route"] == "cold":
        if spec["cached_target"] is not None or spec["local_repair_on"]:
            raise ValueError("cold route cannot start from or locally repair a cached target")
        if ((spec["coarse_origin"] == "model_produced") != (spec["provided_coarse"] is None)):
            raise ValueError("provided coarse must match declared origin")
    elif spec["cached_target"] is None or spec["provided_coarse"] is not None:
        raise ValueError("reuse route requires cached target and no provided coarse")


def run(spec, adapters, *, clock=time.perf_counter_ns, id_factory=None):
    """Run one route; adapters own evidence, authority and actual I/O."""
    _validate_spec(spec)
    if type(adapters) is not dict:
        raise ValueError("adapter mapping required")
    journal = adapters.get("journal", lambda event: None)
    if not callable(journal):
        raise ValueError("journal adapter must be callable")
    id_factory = id_factory or (lambda: uuid.uuid4().hex)
    stages = {name: {"status": "not_reached", "reason": None} for name in ALL_STAGES}
    attempts, model_calls, phases = [], [], []
    selected = cache_update = repair_path = None
    repair_trace = []

    def emit(event): journal(copy.deepcopy(event))

    def local(name, payload):
        stages[name] = {"status": "started", "reason": None}
        started = clock(); emit({"event": "stage_started", "stage": name, "started_ns": started})
        try:
            value = _require_callable(adapters, name)(copy.deepcopy(payload))
        except Exception as error:
            ended = clock(); stages[name] = {"status": "failed", "reason": repr(error)}
            phases.append({"stage": name, "started_ns": started, "ended_ns": ended,
                           "elapsed_ns": ended-started})
            emit({"event": "stage_failed", "stage": name, "ended_ns": ended,
                  "error": repr(error)})
            raise
        ended = clock(); stages[name] = {"status": "completed", "reason": None}
        phases.append({"stage": name, "started_ns": started, "ended_ns": ended,
                       "elapsed_ns": ended-started})
        emit({"event": "stage_completed", "stage": name, "ended_ns": ended})
        return value

    def model(name, payload):
        attempt_id, started = id_factory(), clock()
        attempt = {"attempt_id": attempt_id, "stage": name, "status": "started",
                   "started_ns": started, "completed_ns": None, "call_id": None,
                   "usage": None, "visible_images_submitted": None,
                   "wait_ns": None, "error": None}
        attempts.append(attempt); stages[name] = {"status": "started", "reason": None}
        emit({"event": "model_attempt_started", **copy.deepcopy(attempt)})
        try:
            result = _model_result(_require_callable(adapters, name)(copy.deepcopy(payload)))
        except Exception as error:
            ended = clock()
            attempt.update(status="failed", completed_ns=ended,
                           call_id=getattr(error, "call_id", None),
                           usage=_usage(getattr(error, "usage", None)),
                           visible_images_submitted=_optional_count(
                               getattr(error, "visible_images_submitted", None),
                               "visible_images_submitted"),
                           wait_ns=_optional_count(getattr(error, "wait_ns", None), "wait_ns"),
                           error=repr(error))
            stages[name] = {"status": "failed", "reason": repr(error)}
            phases.append({"stage": name, "started_ns": started, "ended_ns": ended,
                           "elapsed_ns": ended-started})
            emit({"event": "model_attempt_finished", **copy.deepcopy(attempt)})
            raise
        ended = clock()
        attempt.update(status="completed", completed_ns=ended,
                       call_id=result["call_id"], usage=result["usage"],
                       visible_images_submitted=result["visible_images_submitted"],
                       wait_ns=result["wait_ns"])
        stages[name] = {"status": "completed", "reason": None}
        model_calls.append({"attempt_id": attempt_id, "stage": name, **result})
        phases.append({"stage": name, "started_ns": started, "ended_ns": ended,
                       "elapsed_ns": ended-started})
        emit({"event": "model_attempt_finished", **copy.deepcopy(attempt)})
        return result

    def finish(outcome, reason, *, task_effect=None, delivery=None,
               execution_progress=None):
        for row in stages.values():
            if row["status"] == "not_reached": row.update(status="skipped", reason="branch_not_reached")
        call_ids = [row["call_id"] for row in attempts if row["call_id"] is not None]
        duplicates = sorted({v for v in call_ids if call_ids.count(v) > 1})
        coverage = {field: sum(row["usage"] is not None and field in row["usage"]
                               for row in attempts) for field in USAGE_FIELDS}
        totals = {field: (sum(row["usage"][field] for row in attempts
                              if row["usage"] is not None and field in row["usage"])
                          if coverage[field] == len(attempts) else None)
                  for field in USAGE_FIELDS}
        image_coverage = sum(row["visible_images_submitted"] is not None for row in attempts)
        wait_coverage = sum(row["wait_ns"] is not None for row in attempts)
        costs = [row["cost"] for row in model_calls if row["cost"] is not None]
        if spec["route"] == "cold" and spec["coarse_origin"] == "model_produced":
            comparison = {"class": "full_cold", "omitted_stages": [],
                          "comparable_to_full_cold": True}
        elif spec["route"] == "cold":
            comparison = {"class": "injected_subpath", "omitted_stages": ["coarse_model"],
                          "comparable_to_full_cold": False}
        else:
            comparison = {"class": "warm_reuse", "omitted_stages":
                          ["observe_source", "coarse_model", "acquire_anchor", "anchor_model"],
                          "comparable_to_full_cold": False}
        result = {"outcome": outcome, "reason": reason, "task_effect": task_effect,
                  "delivery": delivery, "execution_progress": copy.deepcopy(execution_progress),
                  "selected_target": copy.deepcopy(selected), "cache_update": copy.deepcopy(cache_update),
                  "repair_path": repair_path, "route": spec["route"],
                  "repair_trace": copy.deepcopy(repair_trace),
                  "coarse_origin": spec["coarse_origin"], "comparison": comparison,
                  "stages": stages, "attempt_ledger": attempts,
                  "model_call_ledger": model_calls,
                  "accounting": {"attempted_calls": len(attempts),
                      "completed_calls": len(model_calls), "duplicate_call_ids": duplicates,
                      "usage_totals": totals, "usage_coverage": coverage,
                      "visible_images_submitted": (sum(row["visible_images_submitted"] for row in attempts)
                          if image_coverage == len(attempts) else None),
                      "visible_image_coverage": image_coverage,
                      "model_wait_ns": (sum(row["wait_ns"] for row in attempts)
                          if wait_coverage == len(attempts) else None),
                      "model_wait_coverage": wait_coverage,
                      "cost": sum(costs) if len(costs) == len(model_calls) else None,
                      "cached_input_semantics": "subset of input_tokens; never added to input total"},
                  "phase_timings": phases,
                  "input_authority": ("none" if execution_progress is not None and
                      execution_progress.get("status") == "safe_yield" and
                      execution_progress.get("completed_actions") == 0 else
                      "consumed_by_recorded_execute_stage" if stages["execute"]["status"] == "completed"
                      else "none")}
        emit({"event": "adaptive_route_finished", "outcome": outcome,
              "reason": reason, "repair_path": repair_path,
              "attempted_calls": len(attempts)})
        return result

    def stop(decision): return finish("SAFE_STOP", decision["status"])

    def model_repair(initial_reason, local_decision=None):
        nonlocal selected, cache_update, repair_path
        invalid = local_decision or {"status": initial_reason}
        expanded = local("acquire_expansion", {"invalid": invalid, "target": selected})
        model_result = model("expanded_model", expanded)
        repaired = _decision(model_result["output"], {"target_reference"} | STOP_REASONS)
        repair_trace.append({"stage": "model_reacquisition", "status": repaired["status"]})
        if repaired["status"] != "target_reference": return stop(repaired)
        candidate = repaired["target"]
        current = local("post_model_observe", {"target": candidate,
                                                "model_call_id": model_result["call_id"]})
        checked = _post_model_decision(local("post_model_revalidate", {
            "target": candidate, "current_observation": current,
            "model_call_id": model_result["call_id"]}), model_result["call_id"], current)
        repair_trace.append({"stage": "post_model_revalidate", "status": checked["status"]})
        if checked["status"] != "current_patch_match": return stop(checked)
        selected = checked["target"]; cache_update = selected; repair_path = "model_reacquisition"
        return None

    try:
        if spec["route"] == "cold":
            source = local("observe_source", {"target": spec["target"]})
            if spec["coarse_origin"] == "model_produced":
                coarse = _decision(model("coarse_model", source)["output"], {"candidate"} | STOP_REASONS)
                if coarse["status"] != "candidate": return stop(coarse)
            else:
                coarse = copy.deepcopy(spec["provided_coarse"])
                stages["coarse_model"] = {"status": "skipped", "reason": "coarse_" + spec["coarse_origin"]}
            anchor = local("acquire_anchor", coarse)
            anchor_result = model("anchor_model", anchor)
            anchor_decision = _decision(anchor_result["output"], {"target_reference", "expand_search"} | STOP_REASONS)
            if anchor_decision["status"] in STOP_REASONS: return stop(anchor_decision)
            if anchor_decision["status"] == "target_reference":
                selected = anchor_decision["target"]; cache_update = selected
            else:
                expanded = local("acquire_expansion", anchor_decision)
                expanded_result = model("expanded_model", expanded)
                expanded_decision = _decision(expanded_result["output"], {"target_reference"} | STOP_REASONS)
                if expanded_decision["status"] != "target_reference": return stop(expanded_decision)
                selected = expanded_decision["target"]; cache_update = selected
        else:
            selected = copy.deepcopy(spec["cached_target"])
            reuse = _decision(local("reuse_revalidate", selected), {"revalidated"} | STOP_REASONS)
            repair_trace.append({"stage": "reuse_revalidate", "status": reuse["status"]})
            if reuse["status"] == "revalidated":
                cache_update = selected; repair_path = "none"
            else:
                local_decision = None
                fallback_reason = reuse["status"]
                if fallback_reason in spec["local_repair_on"]:
                    local_decision = _local_repair_decision(local("local_repair", {
                        "invalid": reuse, "target": selected}))
                    repair_trace.append({"stage": "local_repair",
                                         "status": local_decision["status"]})
                    if local_decision["status"] == "repaired":
                        selected = local_decision["target"]; cache_update = selected
                        repair_path = "local"
                    else:
                        fallback_reason = local_decision["status"]
                if repair_path != "local":
                    if fallback_reason not in spec["repair_on"]: return stop({"status": fallback_reason})
                    stopped = model_repair(fallback_reason, local_decision)
                    if stopped is not None: return stopped
        revalidation = _decision(local("final_revalidate", selected), {"revalidated"} | STOP_REASONS)
        if revalidation["status"] != "revalidated": return stop(revalidation)
        if "target" in revalidation:
            if revalidation["target"] is None:
                raise ValueError("revalidated target cannot be null")
            selected = copy.deepcopy(revalidation["target"])
            cache_update = copy.deepcopy(selected)
        execution = _execution_decision(local("execute", {"target": selected, "check": revalidation}))
        if execution["status"] == "safe_yield":
            return finish("EXECUTION_INCOMPLETE", execution["reason"],
                          delivery="confirmed_partial" if execution["completed_actions"] else "not_attempted",
                          execution_progress=execution)
        if execution["status"] != "completed":
            return finish("EXECUTION_INCOMPLETE", execution["status"],
                          delivery=execution["status"], execution_progress=execution)
        effect = _decision(local("verify_effect", execution), {"succeeded", "failed", "unavailable"})
        if effect["status"] != "succeeded":
            return finish("TASK_NOT_VERIFIED", effect["status"], task_effect=effect["status"],
                          delivery="confirmed")
        return finish("TASK_SUCCEEDED", "verified_effect", task_effect="succeeded",
                      delivery="confirmed", execution_progress=execution)
    except ModelFailure as error:
        return finish("TASK_DEFERRED" if error.typed_status == "DEFERRED_UPSTREAM"
                      else "CALLER_FAILED", error.typed_status.lower())
    except Exception as error:
        return finish("CALLER_FAILED", repr(error))
