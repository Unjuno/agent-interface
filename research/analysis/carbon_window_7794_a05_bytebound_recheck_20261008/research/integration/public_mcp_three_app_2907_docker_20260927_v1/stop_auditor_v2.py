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
    identities = load(root / "app-identities.json")
    targets = load(root / "targets.json")
    response_path = root / "mcp-responses" / "01-observe-inkscape.json"
    response_bytes = response_path.read_bytes()
    response = json.loads(response_bytes)
    text_blocks = [row.get("text") for row in response.get("content", []) if row.get("type") == "text"]
    image_blocks = [row for row in response.get("content", []) if row.get("type") == "image"]
    if len(text_blocks) != 1 or len(image_blocks) != 1:
        errors.append("response_block_cardinality")
        payload = {}
    else:
        payload = json.loads(text_blocks[0])
    receipt = payload.get("receipt", {})
    report = receipt.get("report", {})
    raw_report = receipt.get("source", {}).get("raw_report", {})
    session = payload.get("session", {})
    if payload.get("schema") != "agent-interface/review-v1" or receipt.get("schema") != "agent-interface/receipt-view-v1":
        errors.append("unexpected_public_receipt_schema")
    if report.get("status") != "returned" or raw_report.get("status") != "returned":
        errors.append("public_observation_not_returned")
    observation = report.get("observation", {})
    if observation.get("target") != "inkscape" or observation.get("native_window_id") != targets.get("inkscape"):
        errors.append("returned_observation_identity_mismatch")
    if receipt.get("authority") != "none" or raw_report.get("side_effect_authority") is not False or raw_report.get("input_dispatched") is not False:
        errors.append("observation_authority_or_input_not_neutral")
    if session.get("session_id") != raw_report.get("session", {}).get("session_id"):
        errors.append("response_session_id_mismatch")
    png = base64.b64decode(image_blocks[0]["data"], validate=True) if image_blocks else b""
    png_sha = hashlib.sha256(png).hexdigest()
    if not png.startswith(b"\x89PNG\r\n\x1a\n") or image_blocks[0].get("mimeType") != "image/png":
        errors.append("returned_image_not_png")
    artifact = observation.get("artifact", {})
    if artifact.get("sha256") != png_sha or artifact.get("bytes") != len(png):
        errors.append("presented_png_not_bound_to_saved_capture")
    if len(identities) != 3 or len({row.get("window_id") for row in identities}) != 3:
        errors.append("three_app_setup_identity_incomplete")
    if set(targets) != {"inkscape", "calc", "chromium"}:
        errors.append("target_registry_incomplete")
    call_id = payload.get("call_id")
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
    if saved_report.get("observation", {}).get("artifact", {}).get("sha256") != png_sha:
        errors.append("server_png_capture_hash_mismatch")
    close_files = list((root / "server-receipts").glob("session-*-close.json"))
    close = load(close_files[0]) if len(close_files) == 1 else {}
    if len(close_files) != 1 or close.get("session_id") != session.get("session_id"):
        errors.append("transport_shutdown_close_receipt_missing_or_mismatched")
    if close.get("status") != "closed" or close.get("release_attempted") is not False:
        errors.append("transport_shutdown_not_neutral")
    request_count = len(list((root / "server-receipts").glob("*/request.json")))
    if request_count != 1:
        errors.append("formal_backend_call_count_not_one")
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
        "reconstructed": {"outer_schema": payload.get("schema"), "receipt_schema": receipt.get("schema"),
            "raw_observation_status": raw_report.get("status"), "target": observation.get("target"),
            "native_window_id": observation.get("native_window_id"), "session_id": session.get("session_id"),
            "png_bytes": len(png), "png_sha256": png_sha, "mcp_backend_calls": request_count,
            "interface_dispatch_invocations": 0, "formal_sequence_completion": False},
        "classification_note": "The public report schema nests status in receipt.report. The frozen runner checked top-level status and aborted after the first successful Inkscape observe. This raw-only audit does not continue/replay that allocation and does not establish three-app integration PASS or FAIL."
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
