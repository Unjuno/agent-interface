"""Explicit partial success summaries; full retained receipts remain authoritative."""
from copy import deepcopy
import json

from runtime.core_v1.sequence import expand_text_gaps, normalize_observation_regions

SCHEMA = "agent-interface/receipt-view-dispatch-summary-v1"


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def summarize_public_dispatch(view, *, source_program=None):
    call_id = view.get('call_id') if isinstance(view, dict) else None
    if not isinstance(call_id, str) or not call_id:
        return deepcopy(view)
    return _summarize_dispatch(view, {"tool": "interface_results", "arguments": {
        "call_id": call_id, "include_image": False, "compact": True,
        "report_refs": True, "detail": "full"}}, source_program=source_program)


def summarize_cli_dispatch(view, run_directory):
    """Project only when the exact complete raw report is locally recoverable."""
    import hashlib
    from pathlib import Path
    full = deepcopy(view)
    try:
        root = Path(run_directory).absolute()
        report = root / 'report.json'
        data = report.read_bytes()
        source = view['receipt']['source']
        if len(data) != source['bytes'] or hashlib.sha256(data).hexdigest() != source['sha256']:
            return full
        return _summarize_dispatch(view, {"command": "review", "arguments": {
            "report": str(report), "run_directory": str(root),
            "compact": True, "report_refs": True,
            "expected_report_sha256": source["sha256"], "no_image": True}})
    except (OSError, KeyError, TypeError, ValueError):
        return full


def _summarize_dispatch(view, retrieval, *, source_program=None):
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
                or set(raw) - {"schema", "status", "result", "normalization", "compilation", "session", "post_dispatch_inspection"}
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
                ):
            return full
        has_post_image = False
        if "post_dispatch_inspection" in raw or "post_dispatch_inspection" in view:
            inspection = raw["post_dispatch_inspection"]
            if (encoded(inspection) != encoded(view["post_dispatch_inspection"])
                    or inspection.get("status") != "needs_review"
                    or inspection.get("error") is not None
                    or inspection.get("input_dispatched") is not False
                    or inspection.get("authority_granted") is not False
                    or inspection.get("review_request", {}).get("tool") != "interface_review_target"):
                return full
            later = inspection.get("observation_report", {})
            native = later.get("observation", {}) if isinstance(later, dict) else {}
            reference = view.get("image_reference", {})
            stamps = [execution.get("ended_ns")] + [r.get("monotonic_ns") for r in execution["releases"]]
            captured = native.get("capture_started_ns") if isinstance(native, dict) else None
            has_post_image = (later.get("status") == "returned" and later.get("error") is None
                and later.get("input_dispatched") is False and later.get("side_effect_authority") is False
                and isinstance(later.get("observation_id"), str)
                and reference.get("post_dispatch_observation_id") == later["observation_id"]
                and reference.get("capture_phase") == "after_dispatch_release"
                and type(captured) is int and bool(stamps) and all(type(t) is int for t in stamps)
                and captured >= max(stamps))
            if "capture_wait" in inspection:
                wait = inspection["capture_wait"]
                if (not has_post_image
                    or set(wait) != {"requested_ms", "started_ns", "ended_ns", "completed", "update_observed"}
                    or any(type(wait[k]) is not int for k in ("requested_ms", "started_ns", "ended_ns"))
                    or not 0 <= wait["requested_ms"] <= 1000
                    or wait["completed"] is not True or wait["update_observed"] is not None
                    or wait["started_ns"] < max(stamps) or wait["ended_ns"] < wait["started_ns"]
                    or wait["ended_ns"] > captured):
                    return full
            # The complete inspection, including expiry and extensions, stays in
            # the outer view. Only its duplicate inside raw_report is omitted.
        if any(type(execution[k]) is not int or execution[k] < 0 for k in ("started_ns", "ended_ns", "emissions", "program_emissions")):
            return full
        if execution["ended_ns"] < execution["started_ns"] or execution["program_emissions"] > execution["emissions"]:
            return full
        if not execution["releases"] or any(r.get("verified") is not True or r.get("keys_down") != [] or r.get("buttons_down") != [] or "error" in r for r in execution["releases"]):
            return full
        if ((not execution["observations"] and not has_post_image)
                or any("error" in o or "artifact_error" in o for o in execution["observations"])):
            return full
        # Preserve all capture, release and activation records, including extensions.
        # Only bounded source/expansion provenance and exact completed/wait lists are omitted.
        section = raw.get("compilation", raw.get("normalization"))
        using_call_program = section is None
        if using_call_program:
            # The MCP owner passes its pre-invocation copy, never a client-supplied
            # lookup argument or a new request. Full lookup retains that exact call.
            if not has_post_image or not isinstance(source_program, dict):
                return full
            from runtime.core_v1.contract import validate_program
            validate_program(source_program)
            if any(op.get("op") == "observe" for op in source_program["ops"]):
                return full
            section = {"source_program": source_program}
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
        previous_wait_end = execution["started_ns"]
        for wait, (index, duration) in zip(waits, expected):
            if set(wait) != {"operation_index", "requested_ms", "started_ns", "ended_ns", "completed", "kind", "update_observed"}:
                return full
            if any(type(wait[k]) is not int for k in ("operation_index", "requested_ms", "started_ns", "ended_ns")):
                return full
            if (wait["operation_index"] != index or wait["requested_ms"] != duration or wait["started_ns"] < 0
                    or wait["started_ns"] < previous_wait_end
                    or wait["ended_ns"] > execution["ended_ns"]
                    or wait["ended_ns"] < wait["started_ns"] or wait["completed"] is not True
                    or wait["kind"] != "fixed_delay" or wait["update_observed"] is not None):
                return full
            previous_wait_end = wait["ended_ns"]
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
            "retrieve": deepcopy(retrieval)}
        if using_call_program:
            projected["presentation"]["program_provenance"] = (
                "Pre-invocation server call copy; full retrieval includes retained_call.arguments.program. "
                "Source report digest identifies the report, not this separate invocation context.")
        return projected if len(encoded(projected)) < len(encoded(view)) else full
    except (KeyError, TypeError, ValueError, AttributeError):
        return full
