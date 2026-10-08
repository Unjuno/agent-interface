"""Independent one-cell byte-link and result audit; does not import probe code."""
import base64
import hashlib
import json
import struct
import zlib
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def valid_png_filter_bytes(data):
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return False
    offset, compressed, width, height, color_type, bit_depth = 8, bytearray(), None, None, None, None
    while offset < len(data):
        if offset + 12 > len(data):
            return False
        size = struct.unpack(">I", data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        chunk = data[offset + 8:offset + 8 + size]
        crc = struct.unpack(">I", data[offset + 8 + size:offset + 12 + size])[0]
        if len(chunk) != size or zlib.crc32(kind + chunk) & 0xffffffff != crc:
            return False
        if kind == b"IHDR":
            width, height, bit_depth, color_type = struct.unpack(">IIBB", chunk[:10])
        elif kind == b"IDAT":
            compressed.extend(chunk)
        elif kind == b"IEND":
            break
        offset += size + 12
    channels = {0: 1, 2: 3, 4: 2, 6: 4}.get(color_type)
    if not width or not height or bit_depth != 8 or channels is None:
        return False
    try:
        raw = zlib.decompress(compressed)
    except zlib.error:
        return False
    stride = width * channels
    return len(raw) == height * (stride + 1) and all(raw[y * (stride + 1)] in range(5) for y in range(height))


def main():
    root = Path("/audit")
    freeze = json.loads((root / "FREEZE.json").read_text())
    manifest = json.loads((root / "manifest.json").read_text())
    result = json.loads((root / "RESULT.json").read_text())
    request_bytes, response_bytes = (root / "request-01.json").read_bytes(), (root / "response-01.json").read_bytes()
    request, response = json.loads(request_bytes), json.loads(response_bytes)
    bridge = json.loads((root / "BRIDGE_SUMMARY.json").read_text())
    image = (root / "image.png").read_bytes()
    image_b64 = base64.b64decode(request.get("image_png_base64", ""))
    body_bytes = base64.b64decode(response.get("body_base64", ""))
    try:
        body = json.loads(body_bytes)
        answer = json.loads(body["message"]["content"])
    except Exception:
        body, answer = {}, {}
    checks = {
        "formal_mode": result.get("mode") == "FORMAL",
        "one_call": result.get("request_count") == 1 and bridge.get("calls_submitted") == 1 and len(list(root.glob("request-*.json"))) == 1,
        "source_base": result.get("obstac_environment", {}).get("OBSTAC_SOURCE_COMMIT") == freeze["base_commit"],
        "obstac_image_id": result.get("obstac_environment", {}).get("OBSTAC_IMAGE_ID") == freeze["image_id"],
        "prereg_freeze": result.get("preregistration_sha256") == freeze["preregistration_sha256"] == sha((root / "PREREGISTRATION.md").read_bytes()),
        "freeze_hash": result.get("freeze_sha256") == sha((root / "FREEZE.json").read_bytes()),
        "source_hashes": all(sha((root / name).read_bytes()) == value for name, value in freeze["sha256"].items()),
        "request_byte_link": result.get("request_sha256") == sha(request_bytes) == bridge.get("request_sha256"),
        "response_byte_link": result.get("response_sha256") == sha(response_bytes) == bridge.get("response_sha256"),
        "request_contract": request.get("model") == manifest["model"] and request.get("model_digest") == manifest["model_digest"] and request.get("format") == "json",
        "prompt_and_options": request.get("prompt") == manifest["prompt"] and request.get("options") == manifest["options"] and request.get("prompt_sha256") == sha(request["prompt"].encode()),
        "image_bytes": sha(image) == sha(image_b64) == manifest["image_sha256"] == result.get("image_sha256"),
        "png_valid_filter_bytes": valid_png_filter_bytes(image),
        "response_body_hash": response.get("body_sha256") == sha(body_bytes),
        "model_identity": response.get("model_before_digest") == manifest["model_digest"] == response.get("model_digest") and response.get("identity_check") == "OK",
        "no_actions": result.get("action_calls") == 0 and result.get("effect_claims") == 0,
    }
    checks["http_200"] = response.get("transport_status") == "OK" and response.get("http_status") == 200
    checks["response_model_name"] = body.get("model") == manifest["model"]
    checks["exact_ready"] = answer == manifest["expected"]
    mutated = dict(request, prompt_sha256="0" * 64)
    checks["corruption_control"] = mutated["prompt_sha256"] != sha(mutated["prompt"].encode())
    integrity = all(checks[key] for key in (
        "formal_mode", "one_call", "source_base", "obstac_image_id", "prereg_freeze", "freeze_hash",
        "source_hashes", "request_byte_link", "response_byte_link", "request_contract", "prompt_and_options",
        "image_bytes", "png_valid_filter_bytes", "response_body_hash", "model_identity", "no_actions", "corruption_control"))
    if not integrity or not checks["http_200"]:
        decision = "STOP_OBSTAC_OR_IMAGE_TRANSPORT"
    elif not checks["response_model_name"] or not checks["exact_ready"]:
        decision = "FAIL_QWEN_VISION_BACKEND_PROBE"
    else:
        decision = "PASS_QWEN_VISION_BACKEND_PROBE_SCOPED"
    output = {"decision": decision, "checks": checks, "http_status": response.get("http_status"),
              "parsed_answer": answer, "response_body_sha256": response.get("body_sha256")}
    Path("/out/AUDIT.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, sort_keys=True))
    raise SystemExit(0 if decision.startswith("PASS_") else 2)


if __name__ == "__main__":
    main()
