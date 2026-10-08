import argparse
import base64
import copy
import hashlib
import json
from pathlib import Path


EXPECTED = ["inkscape", "calc", "chromium"]


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def audit_bundle(bundle):
    errors = []
    result = bundle["result"]
    identities = bundle["identities"]
    trace = bundle["trace"]
    if result.get("decision") != "PASS_PUBLIC_MCP_THREE_APP_OBSERVE_CLOSE_SCOPED":
        errors.append("decision_not_scoped_pass")
    if result.get("input_operations") != 0 or result.get("model_calls") != 0 or result.get("network_calls") != 0:
        errors.append("nonzero_input_model_or_network")
    if result.get("authority_granted") is not False:
        errors.append("authority_not_false")
    if [row.get("name") for row in identities] != EXPECTED:
        errors.append("app_identity_order_or_count")
    if len({row.get("window_id") for row in identities}) != 3:
        errors.append("native_window_ids_not_distinct")
    for row, expected_class in zip(identities, EXPECTED):
        if row.get("owner_pid") not in row.get("owned_pids_at_binding", []):
            errors.append(f"owner_not_in_launch_tree:{expected_class}")
        if expected_class not in row.get("properties", "").lower():
            errors.append(f"window_class_mismatch:{expected_class}")
        size = row.get("size")
        if not isinstance(size, list) or len(size) != 2 or min(size) < 100:
            errors.append(f"invalid_surface_geometry:{expected_class}")
    calls = trace.get("calls", [])
    if [row.get("target") for row in calls] != EXPECTED:
        errors.append("observation_order_or_count")
    if len({row.get("call_id") for row in calls}) != 3:
        errors.append("observation_call_ids_not_unique")
    all_ids = {row.get("session", {}).get("session_id") for row in calls}
    session_id = trace.get("session_id")
    if all_ids != {session_id} or not session_id:
        errors.append("observation_session_identity_mismatch")
    if trace.get("requested_order") != ["inkscape", "calc", "chromium", "close"]:
        errors.append("requested_sequence_mismatch")
    if len(trace.get("server_processes_during_session", [])) != 1:
        errors.append("stdio_server_process_cardinality")
    if trace.get("server_processes_after_transport_shutdown"):
        errors.append("stdio_server_survived_transport_shutdown")
    close = trace.get("close", {})
    close_payload = close.get("close_report", {})
    if close_payload.get("status") != "closed":
        errors.append("close_status_not_closed")
    if close_payload.get("release_attempted") is not False:
        errors.append("observation_only_close_attempted_release")
    if close_payload.get("connection_close_attempted") is not True:
        errors.append("connection_close_not_attempted")
    if close.get("session", {}).get("session_id") != session_id:
        errors.append("close_session_identity_mismatch")
    if close.get("session", {}).get("state") != "closed":
        errors.append("session_not_closed")
    if close.get("call_id") in {row.get("call_id") for row in calls}:
        errors.append("close_call_id_reused")
    retained = trace.get("retained_reads_after_close", [])
    expected_call_ids = {row.get("call_id") for row in calls} | {close.get("call_id")}
    if {row.get("call_id") for row in retained} != expected_call_ids or len(retained) != 4:
        errors.append("post_close_retained_read_cardinality")
    for row in retained:
        if row.get("status") not in ("returned", "closed"):
            errors.append(f"post_close_retained_status:{row.get('call_id')}")

    messages = bundle["messages"]
    for row in calls:
        name = row["target"]
        raw = messages.get(row["response_file"])
        if raw is None:
            errors.append(f"missing_raw_response:{name}")
            continue
        if hashlib.sha256(raw["bytes"]).hexdigest() != row["response_sha256"]:
            errors.append(f"response_sha_mismatch:{name}")
        response = raw["json"]
        content = response.get("content", [])
        text_blocks = [item.get("text") for item in content if item.get("type") == "text"]
        image_blocks = [item for item in content if item.get("type") == "image"]
        if len(text_blocks) != 1 or len(image_blocks) != 1:
            errors.append(f"response_content_cardinality:{name}")
            continue
        try:
            payload = json.loads(text_blocks[0])
            image = base64.b64decode(image_blocks[0]["data"], validate=True)
            if not image.startswith(b"\x89PNG\r\n\x1a\n"):
                errors.append(f"image_not_png:{name}")
            if hashlib.sha256(image).hexdigest() != row["image_sha256"]:
                errors.append(f"image_sha_mismatch:{name}")
            report = bundle["reports"].get(row["call_id"])
            request = bundle["requests"].get(row["call_id"])
            if request is None or report is None:
                errors.append(f"request_or_report_missing:{name}")
                continue
            if request.get("operation") != "observe" or request.get("arguments", {}).get("target") != name:
                errors.append(f"request_target_or_operation_mismatch:{name}")
            if request.get("session", {}).get("session_id") != session_id:
                errors.append(f"request_session_mismatch:{name}")
            if report.get("status") != "returned" or report.get("session", {}).get("session_id") != session_id:
                errors.append(f"report_status_or_session_mismatch:{name}")
            if report.get("observation", {}).get("status") != "returned":
                errors.append(f"report_observation_not_returned:{name}")
            if report.get("observation", {}).get("observation", {}).get("target") != name:
                errors.append(f"native_observation_target_mismatch:{name}")
            if payload.get("session", {}).get("session_id") != session_id:
                errors.append(f"response_session_mismatch:{name}")
            if payload.get("input_dispatched") is not False or payload.get("side_effect_authority") is not False:
                errors.append(f"response_has_authority_or_input:{name}")
        except Exception as error:
            errors.append(f"response_parse_error:{name}:{type(error).__name__}")

    for call_id, report in bundle["reports"].items():
        if call_id == close.get("call_id"):
            if report.get("status") != "closed" or report.get("session", {}).get("session_id") != session_id:
                errors.append("persisted_close_report_mismatch")
    terminal = result.get("app_process_cleanup", [])
    if not terminal or any(row.get("still_running_pids") for row in terminal):
        errors.append("owned_app_or_display_process_still_running")
    if result.get("owned_mcp_server_processes_after_transport_shutdown"):
        errors.append("owned_mcp_server_still_running")
    if result.get("remaining_running_owned_pids"):
        errors.append("remaining_owned_pid")
    if result.get("x_socket_absent_after_cleanup") is not True:
        errors.append("x11_socket_not_removed")
    return errors


def load_bundle(root):
    root = Path(root)
    trace = load_json(root / "mcp-trace.json")
    identities = load_json(root / "app-identities.json")
    result = load_json(root / "result.json")
    requests, reports, messages = {}, {}, {}
    for call in [*trace.get("calls", []), trace.get("close", {})]:
        call_id = call.get("call_id")
        call_dir = Path(call.get("call_directory", ""))
        if call_id and call_dir.exists():
            req = call_dir / "request.json"
            rep = call_dir / "report.json"
            if req.exists():
                requests[call_id] = load_json(req)
            if rep.exists():
                reports[call_id] = load_json(rep)
    response_files = [row.get("response_file") for row in trace.get("calls", [])]
    response_files += [trace.get("close", {}).get("response_file")]
    response_files += [row.get("response_file") for row in trace.get("retained_reads_after_close", [])]
    for name in response_files:
        if name and Path(name).exists():
            raw = Path(name).read_bytes()
            messages[name] = {"bytes": raw, "json": json.loads(raw)}
    return {"trace": trace, "identities": identities, "result": result,
            "requests": requests, "reports": reports, "messages": messages}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    bundle = load_bundle(args.bundle)
    errors = audit_bundle(bundle)
    controls = {}
    mutations = {}
    for name, mutate in [
        ("divergent-session", lambda b: b["trace"]["calls"][1]["session"].update(session_id="tampered")),
        ("nonzero-input", lambda b: b["result"].update(input_operations=1)),
        ("missing-report", lambda b: b["reports"].pop(b["trace"]["calls"][0]["call_id"], None)),
        ("corrupt-image-payload", lambda b: b["messages"][b["trace"]["calls"][0]["response_file"]]["json"]["content"].__setitem__(1, {"type": "image", "data": "%%%"})),
    ]:
        candidate = copy.deepcopy(bundle)
        mutate(candidate)
        detected = bool(audit_bundle(candidate))
        controls[name] = detected
        mutations[name] = "rejected" if detected else "accepted"
    output = {"decision": "PASS_RAW_AUDIT" if not errors and all(controls.values()) else "HOLD_RAW_AUDIT",
              "errors": errors, "corruption_controls_rejected": controls,
              "corruption_control_count": len(controls),
              "checks": {"clean_run": not errors, "all_mutations_rejected": all(controls.values())}}
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=False)
    raw = json.dumps(output, sort_keys=True, indent=2).encode() + b"\n"
    (out / "audit.json").write_bytes(raw)
    (out / "sha256.txt").write_text(hashlib.sha256(raw).hexdigest() + "  audit.json\n")
    print(json.dumps(output, sort_keys=True))
    return 0 if output["decision"] == "PASS_RAW_AUDIT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
