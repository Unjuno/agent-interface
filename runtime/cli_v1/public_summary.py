"""Explicit partial success summaries; full retained receipts remain authoritative."""
from copy import deepcopy
import json

from runtime.core_v1.sequence import expand_text_gaps, normalize_observation_regions

SCHEMA = "agent-interface/receipt-view-dispatch-summary-v1"


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def summarize_public_dispatch(view):
    """Summarize known completed reports only, without changing images or outcomes."""
    full = deepcopy(view)
    try:
        receipt = view["receipt"]
        source = receipt["source"]
        raw = source["raw_report"]
        result = raw["result"]
        execution = result["execution"]
        outcome = view["outcome_summary"]
        if (receipt["schema"] != "agent-interface/receipt-view-v3-report-ref"
                or receipt["authority"] != "none" or view.get("authority") != "none"
                or receipt["report"] != {"report_ref": "/source/raw_report"}
                or receipt["report_reference"] != "/source/raw_report"
                or set(receipt) != {"schema", "authority", "source", "report", "latest_observations", "events", "record_counts", "omitted_from_view", "scope", "motor_state_validation", "report_reference", "reference_scope"}
                or receipt["latest_observations"] or receipt["events"] or receipt["record_counts"]
                or receipt["omitted_from_view"] != 0
                or receipt["motor_state_validation"] != {"present": False, "accepted": False, "reason": "missing"}
                or set(source) != {"path", "sha256", "bytes", "kind", "raw_report"}
                or set(raw) - {"schema", "status", "result", "normalization", "compilation", "session"}
                or raw["schema"] != "agent-interface/runtime-dispatch-result-v1" or raw["status"] != "returned"
                or set(result) != {"status", "admission", "required_capabilities", "execution", "recovery_required"}
                or result["status"] != "completed" or result["admission"] != "accepted"
                or result["recovery_required"] is not False
                or set(execution) != {"started_ns", "ended_ns", "emissions", "program_emissions", "observations", "releases", "waits", "activations", "completed_ops"}
                or view.get("image_status") != "image"
                or any(view.get(k) is not None for k in ("persistence_error", "presentation"))
                or outcome["execution_status"] != "completed" or outcome["input_release_verified"] is not True
                or any(outcome.get(k) is not None for k in ("error", "cleanup_error", "execution_error", "failure_phase", "failure_detail"))
                or ("session" in view and encoded(raw.get("session")) != encoded(view["session"]))
                or view.get("session", {}).get("recovery_required", False) is not False
                or raw.get("session", {}).get("recovery_required", False) is not False
                or not isinstance(view["call_id"], str) or not view["call_id"]):
            return full
        if any(type(execution[k]) is not int or execution[k] < 0 for k in ("started_ns", "ended_ns", "emissions", "program_emissions")):
            return full
        if execution["ended_ns"] < execution["started_ns"] or execution["program_emissions"] > execution["emissions"]:
            return full
        if not execution["releases"] or any(r.get("verified") is not True or r.get("keys_down") != [] or r.get("buttons_down") != [] or "error" in r for r in execution["releases"]):
            return full
        if not execution["observations"] or any("error" in o or "artifact_error" in o for o in execution["observations"]):
            return full
        # Preserve all capture, release and activation records, including extensions.
        # Only bounded source/expansion provenance and exact completed/wait lists are omitted.
        section = raw.get("compilation", raw.get("normalization"))
        if section is None:
            return full
        if "normalization" in raw:
            norm = raw["normalization"]
            if set(norm) != {"kind", "source_program", "source_operation_indices"} or norm["kind"] != "explicit_observation_region":
                return full
            normalized = deepcopy(norm["source_program"])
            normalized["ops"], indices = normalize_observation_regions(normalized["ops"])
            if encoded(indices) != encoded(norm["source_operation_indices"]):
                return full
            if "compilation" in raw and encoded(normalized) != encoded(section["source_program"]):
                return full
        if "compilation" in raw and (set(section) != {"kind", "source_program", "operation_sources"} or section["kind"] != "bounded_text_gap"):
            return full
        program = section["source_program"]
        if set(program) != {"schema", "program_id", "source", "authority", "terminal", "ops"} or program["schema"] != "agent-interface/program-v1":
            return full
        ops, mapping = expand_text_gaps(program["ops"])
        if "compilation" in raw and encoded(mapping) != encoded(section["operation_sources"]):
            return full
        if encoded(execution["completed_ops"]) != encoded(list(range(len(ops)))):
            return full
        waits = execution["waits"]
        expected = [(i, op["timeout_ms"]) for i, op in enumerate(ops) if op["op"] == "wait_update"]
        if len(waits) != len(expected):
            return full
        for wait, (index, duration) in zip(waits, expected):
            if set(wait) != {"operation_index", "requested_ms", "started_ns", "ended_ns", "completed", "kind", "update_observed"}:
                return full
            if any(type(wait[k]) is not int for k in ("operation_index", "requested_ms", "started_ns", "ended_ns")):
                return full
            if (wait["operation_index"] != index or wait["requested_ms"] != duration or wait["started_ns"] < 0
                    or wait["ended_ns"] < wait["started_ns"] or wait["completed"] is not True
                    or wait["kind"] != "fixed_delay" or wait["update_observed"] is not None):
                return full
        projected = deepcopy(view)
        summary = deepcopy(execution)
        summary.pop("completed_ops")
        summary.pop("waits")
        summary["completed_operation_count"] = len(ops)
        summary["wait_summary"] = {"count": len(waits), "requested_ms_total": sum(w["requested_ms"] for w in waits),
            "recorded_elapsed_ns_total": sum(w["ended_ns"] - w["started_ns"] for w in waits),
            "kind": "fixed_delay", "update_observed": None}
        projected["receipt"] = {"schema": SCHEMA, "authority": "none",
            "source": {k: deepcopy(v) for k, v in source.items() if k != "raw_report"},
            "admission": result["admission"], "required_capabilities": deepcopy(result["required_capabilities"]),
            "execution_summary": summary,
            "scope": "Partial historical summary. Source digest identifies the retained full report, not this summary. No task success or authority."}
        if "session" in raw and "session" not in view:
            # A retained lookup has historical session evidence, not a live owner snapshot.
            projected["receipt"]["reported_session"] = deepcopy(raw["session"])
        projected["presentation"] = {"requested": "summary", "returned": "summary",
            "omitted": ["source programs", "expansion map", "individual waits", "completed operation indices", "duplicate session and receipt metadata"],
            "retrieve": {"tool": "interface_results", "arguments": {"call_id": view["call_id"], "include_image": False,
                "compact": True, "report_refs": True, "detail": "full"}}}
        return projected if len(encoded(projected)) < len(encoded(view)) else full
    except (KeyError, TypeError, ValueError, AttributeError):
        return full
