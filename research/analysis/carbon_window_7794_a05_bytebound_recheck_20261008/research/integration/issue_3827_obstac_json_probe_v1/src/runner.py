"""Single-request probe, executed in an Obstac-attributed isolated container."""
import base64
import hashlib
import json
import os
from pathlib import Path
import struct
import time
import zlib


def sha(data):
    return hashlib.sha256(data).hexdigest()


def png():
    width, height = 448, 280
    rgb = (25, 153, 78)
    pixels = bytearray()
    for y in range(height):
        row = bytearray([255])
        for x in range(width):
            row.extend(rgb if 72 <= x < 376 and 42 <= y < 238 else (238, 240, 242))
        pixels.extend(row)
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    hdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", hdr) + chunk(b"IDAT", zlib.compress(bytes(pixels), 9)) + chunk(b"IEND", b"")


def main():
    src, out, exchange = Path("/task"), Path("/out"), Path("/exchange")
    manifest = json.loads((src / "manifest.json").read_text())
    freeze = json.loads(Path("/freeze/FREEZE.json").read_text())
    prereg_sha = sha(Path("/freeze/PREREGISTRATION.md").read_bytes())
    if prereg_sha != freeze["preregistration_sha256"]:
        raise SystemExit("STOP_OBSTAC_PREREGISTRATION_HASH_MISMATCH")
    checks = {name: sha((src / name).read_bytes()) == expected for name, expected in freeze["sha256"].items()}
    if not all(checks.values()):
        raise SystemExit("STOP_SOURCE_HASH_MISMATCH")
    env_ids = {
        "OBSTAC_SOURCE_COMMIT": os.environ.get("OBSTAC_SOURCE_COMMIT"),
        "OBSTAC_IMAGE_ID": os.environ.get("OBSTAC_IMAGE_ID"),
        "OBSTAC_FREEZE_SHA256": os.environ.get("OBSTAC_FREEZE_SHA256"),
    }
    expected_ids = {
        "OBSTAC_SOURCE_COMMIT": freeze["base_commit"],
        "OBSTAC_IMAGE_ID": freeze["image_id"],
        "OBSTAC_FREEZE_SHA256": sha(Path("/freeze/FREEZE.json").read_bytes()),
    }
    if env_ids != expected_ids:
        raise SystemExit("STOP_OBSTAC_PROVENANCE_ENV_MISMATCH")
    image = png()
    image_sha = sha(image)
    (out / "image.png").write_bytes(image)
    request = {
        "allocation": manifest["allocation"], "issue": manifest["issue"], "call_id": "01",
        "model": manifest["model"], "model_digest": manifest["model_digest"],
        "format": manifest["request_format"], "prompt": manifest["prompt"],
        "prompt_sha256": sha(manifest["prompt"].encode()),
        "image_png_base64": base64.b64encode(image).decode("ascii"),
        "image_sha256": image_sha, "options": manifest["options"],
        "stream": False, "keep_alive": "5m",
    }
    request_bytes = json.dumps(request, sort_keys=True, separators=(",", ":")).encode()
    (exchange / "request-01.json").write_bytes(request_bytes)
    construction = os.environ.get("OBSTAC_CONSTRUCTION") == "1"
    deadline = time.monotonic() + (30 if construction else 180)
    response_path = exchange / "response-01.json"
    while not response_path.exists() and time.monotonic() < deadline:
        time.sleep(0.05)
    if not response_path.exists():
        response = {"transport_status": "RPC_TIMEOUT", "http_status": None,
                    "body_base64": "", "body_sha256": sha(b"")}
        (response_path).write_text(json.dumps(response, sort_keys=True) + "\n")
    response = json.loads(response_path.read_text())
    raw = {
        "allocation": manifest["allocation"], "mode": "CONSTRUCTION" if construction else "FORMAL",
        "source_checks": checks, "obstac_environment": env_ids,
        "preregistration_sha256": prereg_sha,
        "freeze_sha256": sha(Path("/freeze/FREEZE.json").read_bytes()),
        "image_sha256": image_sha, "request_sha256": sha(request_bytes),
        "response_sha256": sha(response_path.read_bytes()), "response": response,
        "request_count": 1, "completed_model_responses": int(not construction and response.get("transport_status") == "OK"),
        "action_calls": 0, "effect_claims": 0,
    }
    (out / ("CONSTRUCTION.json" if construction else "RESULT.json")).write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n")
    (exchange / "DONE").write_text("done\n")
    print(json.dumps({"allocation": raw["allocation"], "mode": raw["mode"],
                      "transport_status": response.get("transport_status"),
                      "http_status": response.get("http_status"),
                      "completed_model_responses": raw["completed_model_responses"]}, sort_keys=True))


if __name__ == "__main__":
    main()
