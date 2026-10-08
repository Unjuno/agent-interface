"""One-cell paired-model probe runner with checked Obstac provenance."""
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


def make_png():
    w, h = 448, 280
    pix = bytearray()
    for y in range(h):
        row = bytearray([0])
        for x in range(w):
            row.extend((25, 153, 78) if 72 <= x < 376 and 42 <= y < 238 else (238, 240, 242))
        pix.extend(row)
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    hdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", hdr) + chunk(b"IDAT", zlib.compress(bytes(pix), 9)) + chunk(b"IEND", b"")


def main():
    src, out, exchange = Path("/task"), Path("/out"), Path("/exchange")
    manifest = json.loads((src / "manifest.json").read_text())
    freeze = json.loads(Path("/freeze/FREEZE.json").read_text())
    prereg_sha = sha(Path("/freeze/PREREGISTRATION.md").read_bytes())
    if prereg_sha != freeze["preregistration_sha256"]:
        raise SystemExit("STOP_PREREGISTRATION_HASH_MISMATCH")
    source_hashes = {name: sha((src / name).read_bytes()) for name in freeze["sha256"]}
    if source_hashes != freeze["sha256"]:
        raise SystemExit("STOP_SOURCE_HASH_MISMATCH")
    env = {key: os.environ.get(key) for key in (
        "OBSTAC_SOURCE_COMMIT", "OBSTAC_IMAGE_ID", "OBSTAC_FREEZE_SHA256")}
    expected_env = {"OBSTAC_SOURCE_COMMIT": freeze["base_commit"],
                    "OBSTAC_IMAGE_ID": freeze["image_id"],
                    "OBSTAC_FREEZE_SHA256": sha(Path("/freeze/FREEZE.json").read_bytes())}
    if env != expected_env:
        raise SystemExit("STOP_OBSTAC_PROVENANCE_MISMATCH")
    image = make_png()
    if sha(image) != manifest["image_sha256"]:
        raise SystemExit("STOP_IMAGE_FIXTURE_HASH_MISMATCH")
    (out / "image.png").write_bytes(image)
    request = {"allocation": manifest["allocation"], "issue": manifest["issue"], "call_id": "01",
               "model": manifest["model"], "model_digest": manifest["model_digest"],
               "format": "json", "prompt": manifest["prompt"], "prompt_sha256": sha(manifest["prompt"].encode()),
               "image_png_base64": base64.b64encode(image).decode("ascii"), "image_sha256": sha(image),
               "options": manifest["options"], "stream": False, "keep_alive": "5m"}
    req_bytes = json.dumps(request, sort_keys=True, separators=(",", ":")).encode()
    (exchange / "request-01.json").write_bytes(req_bytes)
    construction = os.environ.get("OBSTAC_CONSTRUCTION") == "1"
    response_path = exchange / "response-01.json"
    deadline = time.monotonic() + (30 if construction else 180)
    while not response_path.exists() and time.monotonic() < deadline:
        time.sleep(0.05)
    if not response_path.exists():
        response = {"transport_status": "RPC_TIMEOUT", "http_status": None,
                    "body_base64": "", "body_sha256": sha(b""), "model_digest": ""}
        response_path.write_text(json.dumps(response, sort_keys=True) + "\n")
    response = json.loads(response_path.read_text())
    result = {"allocation": manifest["allocation"], "mode": "CONSTRUCTION" if construction else "FORMAL",
              "source_hashes": source_hashes, "obstac_environment": env, "preregistration_sha256": prereg_sha,
              "freeze_sha256": sha(Path("/freeze/FREEZE.json").read_bytes()),
              "request_count": 1, "completed_model_responses": int(not construction and response.get("transport_status") == "OK" and response.get("http_status") == 200),
              "image_sha256": sha(image), "request_sha256": sha(req_bytes),
              "response_sha256": sha(response_path.read_bytes()), "response": response,
              "action_calls": 0, "effect_claims": 0}
    (out / ("CONSTRUCTION.json" if construction else "RESULT.json")).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (exchange / "DONE").write_text("done\n")
    print(json.dumps({"allocation": result["allocation"], "mode": result["mode"],
                      "completed_model_responses": result["completed_model_responses"],
                      "http_status": response.get("http_status"), "transport_status": response.get("transport_status")}, sort_keys=True))


if __name__ == "__main__":
    main()
