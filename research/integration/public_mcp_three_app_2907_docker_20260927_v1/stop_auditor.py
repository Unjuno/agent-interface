import argparse
import base64
import hashlib
import json
from pathlib import Path


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(args.bundle)
    errors = []
    result = load(root / "result.json")
    identity = load(root / "app-identities.json")
    targets = load(root / "targets.json")
    response_bytes = (root / "mcp-responses" / "01-observe-inkscape.json").read_bytes()
    response = json.loads(response_bytes)
    text_blocks = [row.get("text") for row in response.get("content", []) if row.get("type") == "text"]
    image_blocks = [row for row in response.get("content", []) if row.get("type") == "image"]
    if len(text_blocks) != 1 or len(image_blocks) != 1:
        errors.append("response_block_cardinality")
        payload = {}
    else:
        payload = json.loads(text_blocks[0])
    report = payload.get("receipt", {}).get("report", {})
    raw_report = payload.get("receipt", {}).get("source", {}).get("raw_report", {})
    session = payload.get("session", {})
    if report.get("status") != "returned" or raw_report.get("status") != "returned":
        errors.append("public_observation_not_returned")
    if report.get("observation", {}).get("target") != "inkscape":
        errors.append("returned_observation_target_mismatch")
    if report.get("observation", {}).get("native_window_id") != targets.get("inkscape"):
        errors.append("returned_native_window_mismatch")
    if payload.get("schema") != "agent-interface/receipt-view-v1":
        errors.append("unexpected_public_receipt_schema")
    if payload.get("receipt", {}).get("authority") != "none":
        errors.append("receipt_authority_not_none")
    if raw_report.get("side_effect_authority") is not False or raw_report.get("input_dispatched") is not False:
        errors.append("raw_observation_authority_or_input")
    if session.get("session_id") != raw_report.get("session", {}).get("session_id"):
        errors.append("response_session_id_mismatch")
    png = base64.b64decode(image_blocks[0]["data"], validate=True) if image_blocks else b""
    if not png.startswith(b"\x89PNG\r\n\x1a\n"):
        errors.append("returned_image_not_png")
    if len(identity) != 3 or len({row.get("window_id") for row in identity}) != 3:
        errors.append("three_app_setup_identity_incomplete")
    if set(targets) != {"inkscape", "calc", "chromium"}:
        errors.append("target_registry_incomplete")
    request_id = payload.get("call_id")
    call_root = Path(payload.get("call_directory", ""))
    if not call_root.exists():
        errors.append("server_call_directory_missing")
        request, saved_report = {}, {}
    else:
        request = load(call_root / "request.json")
        saved_report = load(call_root / "report.json")
    if request.get("operation") != "observe" or request.get("arguments", {}).get("target") != "inkscape":
        errors.append("persisted_request_mismatch")
    if request.get("session", {}).get("session_id") != session.get("session_id"):
        errors.append("persisted_request_session_mismatch")
    if saved_report.get("status") != "returned" or saved_report.get("session", {}).get("session_id") != session.get("session_id"):
        errors.append("persisted_report_mismatch")
    close_files = list((root / "server-receipts").glob("session-*-close.json"))
    close = load(close_files[0]) if len(close_files) == 1 else {}
    if len(close_files) != 1 or close.get("session_id") != session.get("session_id"):
        errors.append("transport_shutdown_close_receipt_missing_or_mismatched")
    if close.get("status") != "closed" or close.get("release_attempted") is not False:
        errors.append("transport_shutdown_not_neutral")
    if result.get("input_operations") != 0 or result.get("model_calls") != 0 or result.get("network_calls") != 0:
        errors.append("nonzero_input_model_or_network_counter")
    if result.get("owned_mcp_server_processes_after_transport_shutdown"):
        errors.append("mcp_server_survived_transport_shutdown")
    if result.get("x_socket_absent_after_cleanup") is not True or result.get("remaining_running_owned_pids"):
        errors.append("owned_process_or_socket_cleanup_incomplete")
    output = {
        "decision": "PASS_RAW_STOP_AUDIT" if not errors else "HOLD_RAW_STOP_AUDIT",
        "disposition": "STOP_CALLER_RECEIPT_SHAPE_NOT_INTEGRATION_FAIL" if not errors else "HOLD_RAW_STOP_AUDIT",
        "errors": errors,
        "preserved_runner_decision": result.get("decision"),
        "preserved_container_result_sha256": hashlib.sha256((root / "result.json").read_bytes()).hexdigest(),
        "raw_mcp_response_sha256": hashlib.sha256(response_bytes).hexdigest(),
        "reconstructed": {"receipt_schema": payload.get("schema"),
            "raw_observation_status": raw_report.get("status"),
            "target": report.get("observation", {}).get("target"),
            "native_window_id": report.get("observation", {}).get("native_window_id"),
            "session_id": session.get("session_id"), "png_bytes": len(png),
            "png_sha256": hashlib.sha256(png).hexdigest(),
            "interface_dispatch_invocations": 0,
            "mcp_backend_calls": len(list((root / "server-receipts").glob("*/request.json"))),
            "formal_sequence_completion": False},
        "classification_note": "The public API report is nested at receipt.report; the frozen runner only checked top-level status and aborted after the first returned Inkscape observation. This raw-only audit does not continue or replay the allocation and does not establish three-app integration PASS/FAIL."
    }
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=False)
    raw = json.dumps(output, sort_keys=True, indent=2).encode() + b"\n"
    (out / "audit.json").write_bytes(raw)
    (out / "sha256.txt").write_text(hashlib.sha256(raw).hexdigest() + "  audit.json\n")
    print(json.dumps(output, sort_keys=True))
    return 0 if output["decision"] == "PASS_RAW_STOP_AUDIT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
