"""Shared acquisition, reuse, invalidation and repair accounting boundary."""
import copy
import time
import uuid


USAGE_FIELDS = ("input_tokens", "cached_input_tokens",
                "cache_write_input_tokens", "output_tokens",
                "reasoning_output_tokens")
MODEL_STAGES = ("coarse_model", "anchor_model", "expanded_model")
ALL_STAGES = ("observe_source", "coarse_model", "acquire_anchor",
              "anchor_model", "reuse_revalidate", "acquire_expansion",
              "expanded_model", "final_revalidate", "execute",
              "verify_effect")
STOP_REASONS = {"no_match", "search_exhausted", "ambiguous",
                "unavailable", "stale", "association_changed"}


class ModelFailure(RuntimeError):
    def __init__(self, message, *, call_id=None, usage=None):
        super().__init__(message)
        self.call_id = call_id
        self.usage = usage


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


def _model_result(value):
    required = {"call_id", "output", "usage", "requested_model",
                "requested_effort", "cost"}
    if type(value) is not dict or set(value) != required:
        raise ValueError("exact model result fields required")
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
    return result


def _decision(value, allowed):
    if type(value) is not dict or type(value.get("status")) is not str:
        raise ValueError("typed decision object required")
    if value["status"] not in allowed:
        raise ValueError("unsupported decision status " + value["status"])
    if value["status"] in STOP_REASONS and value.get("target") is not None:
        raise ValueError("stop decision must not expose a target")
    return copy.deepcopy(value)


def _validate_spec(spec):
    required = {"target", "route", "coarse_origin", "provided_coarse",
                "cached_target", "repair_on", "session_id"}
    if type(spec) is not dict or set(spec) != required:
        raise ValueError("exact adaptive caller specification required")
    if type(spec["target"]) is not str or not spec["target"]:
        raise ValueError("nonempty target required")
    if spec["route"] not in ("cold", "reuse"):
        raise ValueError("route must be cold or reuse")
    origins = ("model_produced", "caller_provided", "injected_archive")
    if spec["coarse_origin"] not in origins:
        raise ValueError("declared coarse origin required")
    if type(spec["repair_on"]) is not list or any(
            value not in STOP_REASONS for value in spec["repair_on"]):
        raise ValueError("repair_on must contain typed stop reasons")
    if type(spec["session_id"]) is not str or not spec["session_id"]:
        raise ValueError("session id required")
    if spec["route"] == "cold":
        if spec["cached_target"] is not None:
            raise ValueError("cold route cannot start from cached target")
        if ((spec["coarse_origin"] == "model_produced") !=
                (spec["provided_coarse"] is None)):
            raise ValueError("provided coarse must match declared origin")
    else:
        if spec["cached_target"] is None:
            raise ValueError("reuse route requires cached target")
        if spec["provided_coarse"] is not None:
            raise ValueError("reuse route cannot provide coarse point")


def run(spec, adapters, *, clock=time.perf_counter_ns, id_factory=None):
    """Run one typed route; adapters own domain evidence and actual I/O."""
    _validate_spec(spec)
    if type(adapters) is not dict:
        raise ValueError("adapter mapping required")
    journal = adapters.get("journal", lambda event: None)
    if not callable(journal):
        raise ValueError("journal adapter must be callable")
    id_factory = id_factory or (lambda: uuid.uuid4().hex)
    stages = {name: {"status": "not_reached", "reason": None}
              for name in ALL_STAGES}
    attempts = []
    model_calls = []
    phases = []
    selected = None
    cache_update = None

    def emit(event):
        journal(copy.deepcopy(event))

    def local(name, payload):
        stages[name] = {"status": "started", "reason": None}
        started = clock()
        emit({"event": "stage_started", "stage": name, "started_ns": started})
        try:
            value = _require_callable(adapters, name)(copy.deepcopy(payload))
        except Exception as error:
            ended = clock()
            stages[name] = {"status": "failed", "reason": repr(error)}
            phases.append({"stage": name, "started_ns": started,
                           "ended_ns": ended, "elapsed_ns": ended - started})
            emit({"event": "stage_failed", "stage": name,
                  "ended_ns": ended, "error": repr(error)})
            raise
        ended = clock()
        stages[name] = {"status": "completed", "reason": None}
        phases.append({"stage": name, "started_ns": started,
                       "ended_ns": ended, "elapsed_ns": ended - started})
        emit({"event": "stage_completed", "stage": name, "ended_ns": ended})
        return value

    def model(name, payload):
        attempt_id = id_factory()
        started = clock()
        attempt = {"attempt_id": attempt_id, "stage": name,
                   "status": "started", "started_ns": started,
                   "completed_ns": None, "call_id": None,
                   "usage": None, "error": None}
        attempts.append(attempt)
        stages[name] = {"status": "started", "reason": None}
        emit({"event": "model_attempt_started", **copy.deepcopy(attempt)})
        try:
            result = _model_result(
                _require_callable(adapters, name)(copy.deepcopy(payload)))
        except Exception as error:
            ended = clock()
            attempt.update(status="failed", completed_ns=ended,
                           call_id=getattr(error, "call_id", None),
                           usage=_usage(getattr(error, "usage", None)),
                           error=repr(error))
            stages[name] = {"status": "failed", "reason": repr(error)}
            phases.append({"stage": name, "started_ns": started,
                           "ended_ns": ended, "elapsed_ns": ended - started})
            emit({"event": "model_attempt_finished", **copy.deepcopy(attempt)})
            raise
        ended = clock()
        attempt.update(status="completed", completed_ns=ended,
                       call_id=result["call_id"], usage=result["usage"])
        stages[name] = {"status": "completed", "reason": None}
        model_calls.append({"attempt_id": attempt_id, "stage": name, **result})
        phases.append({"stage": name, "started_ns": started,
                       "ended_ns": ended, "elapsed_ns": ended - started})
        emit({"event": "model_attempt_finished", **copy.deepcopy(attempt)})
        return result["output"]

    def finish(outcome, reason, *, task_effect=None, delivery=None):
        for name, row in stages.items():
            if row["status"] == "not_reached":
                row.update(status="skipped", reason="branch_not_reached")
        call_ids = [row["call_id"] for row in attempts
                    if row["call_id"] is not None]
        duplicates = sorted({value for value in call_ids
                             if call_ids.count(value) > 1})
        coverage = {field: sum(row["usage"] is not None and
                               field in row["usage"]
                               for row in attempts)
                    for field in USAGE_FIELDS}
        totals = {field: (sum(row["usage"][field] for row in attempts
                              if row["usage"] is not None and
                              field in row["usage"])
                          if coverage[field] == len(attempts) else None)
                  for field in USAGE_FIELDS}
        costs = [row["cost"] for row in model_calls if row["cost"] is not None]
        cost = sum(costs) if len(costs) == len(model_calls) else None
        if spec["route"] == "cold" and spec["coarse_origin"] == "model_produced":
            comparison_class = "full_cold"
            omitted = []
        elif spec["route"] == "cold":
            comparison_class = "injected_subpath"
            omitted = ["coarse_model"]
        else:
            comparison_class = "warm_reuse"
            omitted = ["observe_source", "coarse_model", "acquire_anchor",
                       "anchor_model"]
        result = {"outcome": outcome, "reason": reason,
                  "task_effect": task_effect, "delivery": delivery,
                  "selected_target": copy.deepcopy(selected),
                  "cache_update": copy.deepcopy(cache_update),
                  "route": spec["route"],
                  "coarse_origin": spec["coarse_origin"],
                  "comparison": {"class": comparison_class,
                      "omitted_stages": omitted,
                      "comparable_to_full_cold": comparison_class == "full_cold"},
                  "stages": stages, "attempt_ledger": attempts,
                  "model_call_ledger": model_calls,
                  "accounting": {"attempted_calls": len(attempts),
                      "completed_calls": len(model_calls),
                      "duplicate_call_ids": duplicates,
                      "usage_totals": totals, "usage_coverage": coverage,
                      "cost": cost,
                      "cached_input_semantics":
                          "subset of input_tokens; never added to input total"},
                  "phase_timings": phases,
                  "input_authority": (
                      "consumed_by_recorded_execute_stage"
                      if stages["execute"]["status"] == "completed" else "none")}
        emit({"event": "adaptive_route_finished", "outcome": outcome,
              "reason": reason, "attempted_calls": len(attempts)})
        return result

    def stop(decision):
        status = decision["status"]
        return finish("SAFE_STOP", status)

    try:
        if spec["route"] == "cold":
            source = local("observe_source", {"target": spec["target"]})
            if spec["coarse_origin"] == "model_produced":
                coarse = _decision(model("coarse_model", source),
                                   {"candidate"} | STOP_REASONS)
                if coarse["status"] != "candidate":
                    return stop(coarse)
            else:
                coarse = copy.deepcopy(spec["provided_coarse"])
                stages["coarse_model"] = {"status": "skipped",
                    "reason": "coarse_" + spec["coarse_origin"]}
            anchor = local("acquire_anchor", coarse)
            anchor_decision = _decision(model("anchor_model", anchor),
                {"target_reference", "expand_search"} | STOP_REASONS)
            if anchor_decision["status"] in STOP_REASONS:
                return stop(anchor_decision)
            if anchor_decision["status"] == "target_reference":
                selected = anchor_decision["target"]
                cache_update = selected
            else:
                expanded = local("acquire_expansion", anchor_decision)
                expanded_decision = _decision(model("expanded_model", expanded),
                    {"target_reference"} | STOP_REASONS)
                if expanded_decision["status"] != "target_reference":
                    return stop(expanded_decision)
                selected = expanded_decision["target"]
                cache_update = selected
        else:
            selected = copy.deepcopy(spec["cached_target"])
            reuse = _decision(local("reuse_revalidate", selected),
                              {"revalidated"} | STOP_REASONS)
            if reuse["status"] != "revalidated":
                if reuse["status"] not in spec["repair_on"]:
                    return stop(reuse)
                expanded = local("acquire_expansion", {"invalid": reuse,
                                                        "target": selected})
                repaired = _decision(model("expanded_model", expanded),
                                     {"target_reference"} | STOP_REASONS)
                if repaired["status"] != "target_reference":
                    return stop(repaired)
                selected = repaired["target"]
                cache_update = selected
            else:
                cache_update = selected
        revalidation = _decision(local("final_revalidate", selected),
                                 {"revalidated"} | STOP_REASONS)
        if revalidation["status"] != "revalidated":
            return stop(revalidation)
        execution = _decision(local("execute", {"target": selected,
                                                  "check": revalidation}),
                              {"completed", "delivery_uncertain", "failed"})
        if execution["status"] != "completed":
            return finish("EXECUTION_INCOMPLETE", execution["status"],
                          delivery=execution["status"])
        effect = _decision(local("verify_effect", execution),
                           {"succeeded", "failed", "unavailable"})
        if effect["status"] != "succeeded":
            return finish("TASK_NOT_VERIFIED", effect["status"],
                          task_effect=effect["status"], delivery="confirmed")
        return finish("TASK_SUCCEEDED", "verified_effect",
                      task_effect="succeeded", delivery="confirmed")
    except Exception as error:
        return finish("CALLER_FAILED", repr(error))
