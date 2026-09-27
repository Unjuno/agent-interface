"""Container runner: compose frozen channels, RPC locally, and retain raw rows."""
import base64
import hashlib
import json
import os
from pathlib import Path
import sys
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
    colors = {"green": (25, 153, 78), "red": (205, 47, 54)}
    fill = colors[color]
    pixels = bytearray()
    for y in range(height):
        row = bytearray([255])
        for x in range(width):
            if 72 <= x < 376 and 42 <= y < 238:
                row.extend(fill)
            else:
                row.extend((238, 240, 242))
        pixels.extend(row)
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(bytes(pixels), 9)) + chunk(b"IEND", b"")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def make_prompt(scenario, policy_name, bundle, skew):
    records_text = [{k: v for k, v in row.items() if k != "color"} for row in bundle]
    return (
        "You are a narrow visual status reader. The screenshot contains a large badge: "
        "green means READY; red means BLOCKED. The requested target is task-A. "
        "Use the channel records and their task_id, epoch, capture_ms and arrival_ms. "
        "If records for task-A conflict across epochs, have duplicate state channels, "
        "or cannot support one current status, return ABSTAIN. Otherwise return the "
        "status supported by coherent evidence. Return only JSON {\"answer\": "
        "\"READY\"|\"BLOCKED\"|\"ABSTAIN\"}.\n"
        f"Scenario={scenario}; policy={policy_name}; measured_capture_skew_ms={skew}; "
        f"channels={json.dumps(records_text, sort_keys=True, separators=(',', ':'))}"
    )


def parse_response(response):
    try:
        message = response["message"]["content"]
        value = json.loads(message)
        if set(value) != {"answer"} or value["answer"] not in {"READY", "BLOCKED", "ABSTAIN"}:
            raise ValueError("schema mismatch")
        return value["answer"], None
    except Exception as exc:
        return None, f"INVALID_MODEL_OUTPUT:{type(exc).__name__}:{exc}"


def wait_response(exchange, call_id, timeout=240):
    path = exchange / f"response-{call_id}.json"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            return json.loads(path.read_text())
        time.sleep(0.1)
    return {"status": "STOP_RPC_TIMEOUT", "call_id": call_id}


def main():
    study = Path("/src")
    output = Path("/out")
    exchange = Path("/exchange")
    freeze = json.loads(Path("/freeze/FREEZE.json").read_text())
    manifest_path = study / "manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    source_checks = {}
    for rel, expected in freeze["sha256"].items():
        got = sha((study / rel).read_bytes())
        source_checks[rel] = {"expected": expected, "observed": got, "match": expected == got}
    if not all(v["match"] for v in source_checks.values()):
        raise SystemExit("STOP_SOURCE_HASH_MISMATCH")
    rows = []
    call_number = 0
    images = output / "images"
    images.mkdir(parents=True, exist_ok=True)
    for scenario in manifest["scenarios"]:
        image = png(scenario["image"]["color"])
        image_path = images / f"{scenario['id']}.png"
        image_path.write_bytes(image)
        image_sha = sha(image)
        for policy_name in POLICIES:
            decision = compose(scenario, policy_name, manifest["max_skew_ms"])
            cap = [scenario["image"]["capture_ms"], *[r["capture_ms"] for r in scenario["channels"]]]
            measured_skew = max(cap) - min(cap)
            row = {
                "scenario": scenario["id"], "policy": policy_name,
                "expected": scenario["expected"], "disposition": decision["disposition"],
                "input_epoch_set": sorted({r["epoch"] for r in [scenario["image"], *scenario["channels"]]}),
                "measured_capture_skew_ms": measured_skew,
                "image_sha256": image_sha, "image_bytes": len(image),
                "authority": decision["authority"], "model_called": False,
                "answer": "ABSTAIN" if decision["disposition"] == "ABSTAIN_BEFORE_MODEL" else None,
                "model_error": None,
            }
            if decision["disposition"] != "ABSTAIN_BEFORE_MODEL":
                call_number += 1
                call_id = f"{call_number:02d}"
                prompt = make_prompt(scenario["id"], policy_name, decision["bundle"], measured_skew)
                request = {
                    "call_id": call_id, "allocation": manifest["allocation"],
                    "model": freeze["model"], "model_digest": freeze["model_digest"],
                    "prompt": prompt, "prompt_sha256": sha(prompt.encode()),
                    "image_path": f"images/{scenario['id']}.png", "image_sha256": image_sha,
                    "options": freeze["options"], "answer_schema": manifest["answer_schema"],
                }
                request_path = exchange / f"request-{call_id}.json"
                request_path.write_bytes(canonical(request))
                response = wait_response(exchange, call_id)
                row["model_called"] = True
                row["call_id"] = call_id
                row["request_sha256"] = sha(canonical(request))
                row["response"] = response
                if response.get("status") != "OK":
                    row["model_error"] = response.get("status", "MODEL_RPC_ERROR")
                else:
                    row["answer"], row["model_error"] = parse_response(response["ollama_response"])
                    row["correct"] = row["answer"] == row["expected"]
            else:
                row["correct"] = row["answer"] == row["expected"]
            rows.append(row)
    called = [r for r in rows if r["model_called"]]
    summary = {}
    for policy_name in POLICIES:
        subset = [r for r in rows if r["policy"] == policy_name]
        summary[policy_name] = {
            "rows": len(subset), "correct": sum(r.get("correct") is True for r in subset),
            "expected_answers": len(subset), "abstain_count": sum(r.get("answer") == "ABSTAIN" for r in subset),
            "model_calls": sum(r["model_called"] for r in subset),
        }
    construction = os.environ.get("CONSTRUCTION_ONLY") == "1"
    result = {
        "allocation": manifest["allocation"], "disposition": "RESULT_REQUIRES_INDEPENDENT_AUDIT",
        "run_mode": "CONSTRUCTION_ONLY" if construction else "FORMAL",
        "base_commit": freeze["base_commit"], "freeze_sha256": sha(Path("/freeze/FREEZE.json").read_bytes()),
        "source_checks": source_checks, "scenario_count": len(manifest["scenarios"]),
        "policy_count": len(POLICIES), "model_calls": len(called), "action_calls": 0,
        "effect_claims": 0, "rows": rows, "summary": summary,
    }
    result_name = "CONSTRUCTION.json" if construction else "RESULT.json"
    (output / result_name).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (exchange / "DONE").write_text("done\n")
    print(json.dumps({"allocation": result["allocation"], "model_calls": len(called), "rows": len(rows), "summary": summary}, sort_keys=True))
    if len(rows) != 12 or len(called) != 9:
        raise SystemExit("FAIL_UNEXPECTED_ROW_OR_MODEL_CALL_COUNT")


if __name__ == "__main__":
    main()
