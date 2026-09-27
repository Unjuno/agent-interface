"""Network-isolated 12-cell runner; all local model traffic crosses file RPC."""
import base64
import hashlib
import json
import os
from pathlib import Path
import struct
import time
import zlib

from policy import POLICIES, compose


def sha(data):
    return hashlib.sha256(data).hexdigest()


def chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)


def png(color):
    width, height = 448, 280
    fill = {"green": (25, 153, 78), "red": (205, 47, 54)}[color]
    pixels = bytearray()
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            row.extend(fill if 72 <= x < 376 and 42 <= y < 238 else (238, 240, 242))
        pixels.extend(row)
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(bytes(pixels), 9)) + chunk(b"IEND", b"")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def prompt_for(scenario, policy_name, bundle, skew):
    records_text = [{k: v for k, v in row.items() if k != "color"} for row in bundle]
    return ("You are a narrow visual status reader. The screenshot has a large badge: green means READY; red means BLOCKED. "
            "Requested target task-A. Use task_id, epoch, capture_ms and arrival_ms. If records conflict across epochs, "
            "contain duplicate state channels, or cannot support one current status, return ABSTAIN. Otherwise return "
            'the status supported by coherent evidence. Return only JSON {"answer":"READY"|"BLOCKED"|"ABSTAIN"}.\n'
            f"Scenario={scenario}; policy={policy_name}; measured_capture_skew_ms={skew}; "
            f"channels={json.dumps(records_text, sort_keys=True, separators=(',', ':'))}")


def wait_response(exchange, call_id, timeout=240):
    path = exchange / f"response-{call_id}.json"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            return json.loads(path.read_text())
        time.sleep(0.05)
    return {"status": "STOP_RPC_TIMEOUT", "call_id": call_id}


def parse_response(response):
    try:
        body = response["ollama_response"]
        value = json.loads(body["message"]["content"])
        if set(value) != {"answer"} or value["answer"] not in {"READY", "BLOCKED", "ABSTAIN"}:
            raise ValueError("schema mismatch")
        return value["answer"], None
    except Exception as exc:
        return None, f"INVALID_MODEL_OUTPUT:{type(exc).__name__}:{exc}"


def main():
    study, output, exchange = Path("/src"), Path("/out"), Path("/exchange")
    freeze = json.loads(Path("/freeze/FREEZE.json").read_text())
    manifest = json.loads((study / "manifest.json").read_text())
    source_checks = {rel: sha((study / rel).read_bytes()) == expected for rel, expected in freeze["sha256"].items()}
    if not all(source_checks.values()):
        raise SystemExit("STOP_SOURCE_HASH_MISMATCH")
    prereg_sha = sha(Path("/freeze/PREREGISTRATION.md").read_bytes())
    if prereg_sha != freeze["preregistration_sha256"]:
        raise SystemExit("STOP_PREREGISTRATION_HASH_MISMATCH")
    env = {key: os.environ.get(key) for key in ("OBSTAC_SOURCE_COMMIT", "OBSTAC_IMAGE_ID", "OBSTAC_FREEZE_SHA256")}
    expected_env = {"OBSTAC_SOURCE_COMMIT": freeze["base_commit"], "OBSTAC_IMAGE_ID": freeze["image_id"],
                    "OBSTAC_FREEZE_SHA256": sha(Path("/freeze/FREEZE.json").read_bytes())}
    if env != expected_env:
        raise SystemExit("STOP_OBSTAC_PROVENANCE_MISMATCH")
    construction = os.environ.get("CONSTRUCTION_ONLY") == "1"
    rows, calls, images = [], 0, output / "images"
    images.mkdir(parents=True, exist_ok=True)
    stop = None
    for scenario in manifest["scenarios"]:
        image_bytes = png(scenario["image"]["color"])
        image_sha = sha(image_bytes)
        (images / f"{scenario['id']}.png").write_bytes(image_bytes)
        captures = [scenario["image"]["capture_ms"], *[r["capture_ms"] for r in scenario["channels"]]]
        skew = max(captures) - min(captures)
        for policy_name in POLICIES:
            decision = compose(scenario, policy_name, manifest["max_skew_ms"])
            row = {"scenario": scenario["id"], "policy": policy_name, "expected": scenario["expected"],
                   "disposition": decision["disposition"], "input_epoch_set": sorted({r["epoch"] for r in [scenario["image"], *scenario["channels"]]}),
                   "measured_capture_skew_ms": skew, "image_sha256": image_sha, "image_bytes": len(image_bytes),
                   "authority": decision["authority"], "model_called": False, "answer": None, "model_error": None}
            if decision["disposition"] == "ABSTAIN_BEFORE_MODEL":
                row["answer"], row["correct"] = "ABSTAIN", scenario["expected"] == "ABSTAIN"
                rows.append(row)
                continue
            if stop:
                row["model_error"] = "NOT_RUN_AFTER_STOP"
                rows.append(row)
                continue
            calls += 1
            call_id = f"{calls:02d}"
            prompt = prompt_for(scenario["id"], policy_name, decision["bundle"], skew)
            request = {"call_id": call_id, "allocation": manifest["allocation"], "model": freeze["model"],
                       "model_digest": freeze["model_digest"], "prompt": prompt, "prompt_sha256": sha(prompt.encode()),
                       "image_png_base64": base64.b64encode(image_bytes).decode("ascii"), "image_sha256": image_sha,
                       "options": freeze["options"], "format": "json", "stream": False, "keep_alive": "5m"}
            request_bytes = canonical(request)
            request_path = exchange / f"request-{call_id}.json"
            request_path.write_bytes(request_bytes)
            response = wait_response(exchange, call_id)
            row.update({"model_called": not construction, "request_emitted": True, "call_id": call_id,
                        "request_sha256": sha(request_bytes), "response": response})
            if response.get("status") not in {"OK", "MOCK_CONSTRUCTION_ONLY"}:
                row["model_error"] = response.get("status")
                stop = response.get("status")
            else:
                row["answer"], row["model_error"] = parse_response(response)
                row["correct"] = row["answer"] == scenario["expected"]
            rows.append(row)
            if stop:
                break
        if stop:
            break
    # Model STOP leaves an explicit partial grid; success must produce all 12 rows and 9 calls.
    (exchange / "DONE").write_text("done\n")
    summaries = {}
    for policy_name in POLICIES:
        group = [r for r in rows if r["policy"] == policy_name]
        summaries[policy_name] = {"rows": len(group), "correct": sum(r.get("correct") is True for r in group),
                                  "model_calls": sum(r["model_called"] for r in group),
                                  "abstain_count": sum(r.get("answer") == "ABSTAIN" for r in group)}
    result = {"allocation": manifest["allocation"], "issue": manifest["issue"], "run_mode": "CONSTRUCTION_ONLY" if construction else "FORMAL",
              "base_commit": freeze["base_commit"], "freeze_sha256": sha(Path("/freeze/FREEZE.json").read_bytes()),
              "preregistration_sha256": prereg_sha, "obstac_environment": env, "source_checks": source_checks,
              "scenario_count": len(manifest["scenarios"]), "policy_count": len(POLICIES), "rows": rows,
              "rpc_requests": sum(r.get("request_emitted", False) for r in rows),
              "model_calls": sum(r["model_called"] for r in rows), "completed_responses": sum(r.get("response", {}).get("status") in {"OK", "MOCK_CONSTRUCTION_ONLY"} for r in rows),
              "action_calls": 0, "effect_claims": 0, "stop": stop, "summary": summaries}
    (output / ("CONSTRUCTION.json" if construction else "RESULT.json")).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"allocation": result["allocation"], "mode": result["run_mode"], "rows": len(rows),
                      "model_calls": result["model_calls"], "completed_responses": result["completed_responses"], "stop": stop}, sort_keys=True))
    if not stop and (len(rows) != 12 or result["rpc_requests"] != 9 or (not construction and result["model_calls"] != 9)):
        raise SystemExit("FAIL_UNEXPECTED_GRID_OR_CALL_COUNT")


if __name__ == "__main__":
    main()
