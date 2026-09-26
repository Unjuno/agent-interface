"""Independent integrity and narrow decision audit; stdlib only."""
import base64
import hashlib
import json
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    root = Path("/audit")
    freeze = json.loads((root / "FREEZE.json").read_text())
    manifest = json.loads((root / "manifest.json").read_text())
    result = json.loads((root / "RESULT.json").read_text())
    request_bytes = (root / "request-01.json").read_bytes()
    response_bytes = (root / "response-01.json").read_bytes()
    request = json.loads(request_bytes)
    response = json.loads(response_bytes)
    bridge = json.loads((root / "BRIDGE_SUMMARY.json").read_text())
    checks = {
        "formal_mode": result.get("mode") == "FORMAL",
        "one_request_only": result.get("request_count") == 1 and bridge.get("calls_submitted") == 1,
        "source_commit_bound": result.get("obstac_environment", {}).get("OBSTAC_SOURCE_COMMIT") == freeze["base_commit"],
        "image_identity_bound": result.get("obstac_environment", {}).get("OBSTAC_IMAGE_ID") == freeze["image_id"],
        "freeze_bound": result.get("freeze_sha256") == sha((root / "FREEZE.json").read_bytes()),
        "preregistration_bound": result.get("preregistration_sha256") == freeze["preregistration_sha256"] == sha((root / "PREREGISTRATION.md").read_bytes()),
        "manifest_hashes": all(sha((root / name).read_bytes()) == value for name, value in freeze["sha256"].items()),
        "request_result_hash": result.get("request_sha256") == sha(request_bytes) == bridge.get("request_sha256"),
        "response_result_hash": result.get("response_sha256") == sha(response_bytes) == bridge.get("response_sha256"),
        "request_contract": request.get("format") == "json" and request.get("model_digest") == manifest["model_digest"],
        "request_matches_manifest": request.get("prompt") == manifest["prompt"] and request.get("options") == manifest["options"],
        "one_raw_request_file": len(list(root.glob("request-*.json"))) == 1,
        "prompt_hash": request.get("prompt_sha256") == sha(request["prompt"].encode()),
        "image_hash": request.get("image_sha256") == result.get("image_sha256") == sha((root / "image.png").read_bytes()),
        "response_body_hash": response.get("body_sha256") == sha(base64.b64decode(response.get("body_base64", ""))),
        "no_actions": result.get("action_calls") == 0 and result.get("effect_claims") == 0,
        "response_model_identity": response.get("model_digest") == manifest["model_digest"],
    }
    try:
        body = json.loads(base64.b64decode(response["body_base64"]))
        answer = json.loads(body["message"]["content"])
    except Exception:
        body, answer = {}, {}
    checks["http_200"] = response.get("http_status") == 200 and response.get("transport_status") == "OK"
    checks["response_name"] = body.get("model") == manifest["model"]
    checks["exact_expected_answer"] = answer == manifest["expected"]
    mutated = dict(request, prompt_sha256="0" * 64)
    checks["corruption_control"] = sha(mutated["prompt"].encode()) != mutated["prompt_sha256"]
    integrity = all(checks[key] for key in (
        "formal_mode", "one_request_only", "source_commit_bound", "image_identity_bound", "freeze_bound",
        "manifest_hashes", "preregistration_bound", "request_result_hash", "response_result_hash", "request_contract", "request_matches_manifest", "one_raw_request_file", "prompt_hash",
        "image_hash", "response_body_hash", "no_actions", "response_model_identity", "response_name", "corruption_control"))
    if not integrity or response.get("transport_status") != "OK" or response.get("http_status") != 200:
        decision = "STOP_OBSTAC_OR_MODEL_TRANSPORT"
    elif not checks["response_name"] or not checks["exact_expected_answer"]:
        decision = "FAIL_LOCAL_VISION_JSON_MODE_PROBE"
    else:
        decision = "PASS_LOCAL_VISION_JSON_MODE_PROBE_SCOPED"
    output = {"decision": decision, "checks": checks, "parsed_answer": answer,
              "http_status": response.get("http_status"), "response_body_sha256": response.get("body_sha256")}
    Path("/out/AUDIT.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, sort_keys=True))
    raise SystemExit(0 if decision.startswith("PASS_") else 2)


if __name__ == "__main__":
    main()
