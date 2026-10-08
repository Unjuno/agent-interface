from __future__ import annotations

import base64
import hashlib
import json
import math
import os
import platform
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from renderer import save_pair


MODEL = "qwen2.5vl:7b"
MODEL_DIGEST = "5ced39dfa4bac325dc183dd1e4febaa1c46b3ea28bce48896c8e69c1e79611cc"
API = "http://host.docker.internal:11434"
DIFFICULTY = 0.35
CONSTRUCTION_SEED = 8866600
FORMAL_SEEDS = (8866601, 8866602, 8866603, 8866604, 8866605, 8866606,
                8866607, 8866608, 8866609, 8866610, 8866611, 8866612)
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]


def http_json(url: str, payload: dict[str, Any] | None = None, *, timeout: float = 180) -> tuple[dict[str, Any], float]:
    data = None if payload is None else json.dumps(payload, separators=(",", ":")).encode()
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"} if data else {})
    start = time.monotonic_ns()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        result = json.loads(response.read())
    return result, (time.monotonic_ns() - start) / 1e9


def verify_model() -> dict[str, Any]:
    tags, _ = http_json(f"{API}/api/tags", timeout=5)
    matches = [row for row in tags.get("models", []) if row.get("name") == MODEL]
    if len(matches) != 1 or matches[0].get("digest") != MODEL_DIGEST:
        raise RuntimeError(f"STOP_MODEL_DIGEST_MISMATCH: expected {MODEL_DIGEST}; matches={matches}")
    return {"name": MODEL, "digest": matches[0]["digest"], "size": matches[0].get("size")}


def verify_freeze() -> dict[str, Any]:
    freeze_path = HERE / "FREEZE.json"
    if not freeze_path.is_file():
        raise RuntimeError("STOP_FREEZE_MISSING")
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if freeze.get("model", {}).get("digest") != MODEL_DIGEST or freeze.get("formal_seeds") != list(FORMAL_SEEDS):
        raise RuntimeError("STOP_FREEZE_MODEL_OR_SEED_MISMATCH")
    if freeze.get("container", {}).get("image_id") != os.environ.get("EXPERIMENT_IMAGE_ID"):
        raise RuntimeError("STOP_CONTAINER_IMAGE_ID_MISMATCH")
    if platform.machine().lower() not in {"aarch64", "arm64"}:
        raise RuntimeError(f"STOP_CONTAINER_ARCH_MISMATCH: {platform.machine()}")
    for relative, expected in freeze.get("source_hashes", {}).items():
        path = REPO_ROOT / relative
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"STOP_FROZEN_SOURCE_MISMATCH: {relative}")
    return freeze


def prompt_for(instruction: str) -> str:
    wanted = instruction.removeprefix("TARGET: ").removeprefix("click the ").removesuffix(".")
    return (f"Locate the object described as {wanted}. Return the object's visual center in SOURCE-image pixel coordinates. "
            "The image is 640 pixels wide and 480 pixels high; origin (0,0) is the top-left. "
            "Return JSON only with keys color, shape, x, y. x and y must be numbers.")


def one_request(seed: int, arm: str, image_path: Path, prompt: str, out: Path, order: int) -> dict[str, Any]:
    image = image_path.read_bytes()
    body = {"model": MODEL, "prompt": prompt, "images": [base64.b64encode(image).decode("ascii")],
            "stream": False, "format": {"type": "object", "properties": {
                "color": {"type": "string"}, "shape": {"type": "string"},
                "x": {"type": "number"}, "y": {"type": "number"}},
                "required": ["color", "shape", "x", "y"]},
            "options": {"temperature": 0, "seed": 424242, "num_predict": 128}}
    response, wall_seconds = http_json(f"{API}/api/generate", body)
    raw = response.get("response", "")
    try:
        proposal = json.loads(raw)
        parse_error = None
    except (json.JSONDecodeError, TypeError) as exc:
        proposal, parse_error = None, f"{type(exc).__name__}: {exc}"
    record = {"schema": "arena-v0-grid-localization-call-v1", "seed": seed, "difficulty": DIFFICULTY,
              "arm": arm, "order": order, "model": response.get("model"), "model_digest": MODEL_DIGEST,
              "prompt": prompt, "image_path": image_path.name,
              "image_sha256": hashlib.sha256(image).hexdigest(), "request_sha256": hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
              "request": body, "response": response, "wall_seconds": wall_seconds,
              "proposal": proposal, "parse_error": parse_error, "recorded_utc": datetime.now(timezone.utc).isoformat()}
    out.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")
    return record


def construction() -> int:
    out = HERE / "construction" / "seed-8866600"
    if out.exists():
        raise SystemExit("STOP_CONSTRUCTION_OUTPUT_EXISTS; do not overwrite or retry")
    truth = save_pair(out, CONSTRUCTION_SEED, DIFFICULTY)
    model = verify_model()
    prompt = prompt_for(truth["instruction"])
    warmup = one_request(CONSTRUCTION_SEED, "RAW", out / "raw.png", prompt, out / "construction-call.json", 0)
    grid = one_request(CONSTRUCTION_SEED, "GRID80", out / "grid80.png", prompt, out / "grid80-call.json", 1)
    result = {"status": "CONSTRUCTION_ONLY", "seed": CONSTRUCTION_SEED, "model": model,
              "raw_parse_error": warmup["parse_error"], "grid_parse_error": grid["parse_error"],
              "raw_proposal": warmup["proposal"], "grid_proposal": grid["proposal"],
              "formal_seeds_touched": []}
    (out / "CONSTRUCTION.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


def formal() -> int:
    out = HERE / "formal" / "001"
    try:
        freeze = verify_freeze()
        model = verify_model()
    except Exception as exc:
        print(json.dumps({"status": "STOP_PREFORMAL", "reason": f"{type(exc).__name__}: {exc}"}, sort_keys=True))
        return 2
    out.mkdir(parents=True, exist_ok=False)
    state: dict[str, Any] = {"status": "RUNNING", "allocation": "arena-v0-target-grid-4666-v1-20260927-01",
                             "started_utc": datetime.now(timezone.utc).isoformat(), "model": model,
                             "freeze_sha256": hashlib.sha256((HERE / "FREEZE.json").read_bytes()).hexdigest(),
                             "container_image_id": freeze["container"]["image_id"], "calls_completed": 0}
    (out / "RUN_STATE.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    try:
        warm_truth = save_pair(out / "warmup", CONSTRUCTION_SEED, DIFFICULTY)
        warm_prompt = prompt_for(warm_truth["instruction"])
        warm_call = one_request(CONSTRUCTION_SEED, "EXCLUDED_WARMUP", out / "warmup" / "raw.png", warm_prompt,
                                out / "warmup" / "warmup-call.json", 0)
        (out / "warmup" / "truth.json").write_text(json.dumps(warm_truth, sort_keys=True) + "\n", encoding="utf-8")
        state["warmup_parse_error"] = warm_call["parse_error"]
        if warm_call["parse_error"]:
            raise RuntimeError("STOP_WARMUP_OUTPUT_INVALID")
        calls = out / "calls"
        calls.mkdir()
        for pair_index, seed in enumerate(FORMAL_SEEDS):
            case_dir = calls / f"case-{pair_index + 1:02d}-{seed}"
            truth = save_pair(case_dir, seed, DIFFICULTY)
            (case_dir / "truth.json").write_text(json.dumps(truth, sort_keys=True) + "\n", encoding="utf-8")
            prompt = prompt_for(truth["instruction"])
            arms = ("RAW", "GRID80") if pair_index % 2 == 0 else ("GRID80", "RAW")
            images = {"RAW": case_dir / "raw.png", "GRID80": case_dir / "grid80.png"}
            for order, arm in enumerate(arms):
                call_path = case_dir / f"{arm.lower()}-call.json"
                rec = one_request(seed, arm, images[arm], prompt, call_path, order)
                state["calls_completed"] += 1
                (out / "RUN_STATE.json").write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                if rec["parse_error"]:
                    raise RuntimeError(f"STOP_INVALID_MODEL_JSON seed={seed} arm={arm}")
        state.update({"status": "CAPTURED", "completed_utc": datetime.now(timezone.utc).isoformat()})
    except Exception as exc:
        state.update({"status": "STOP", "stop_reason": f"{type(exc).__name__}: {exc}",
                      "stopped_utc": datetime.now(timezone.utc).isoformat()})
        (out / "STOP.json").write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "RUN_STATE.json").write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(state, sort_keys=True))
    return 0 if state["status"] == "CAPTURED" else 2


def main() -> int:
    if os.environ.get("ARENA_GRID_MODE") == "construction":
        return construction()
    if os.environ.get("ARENA_GRID_MODE") == "formal":
        return formal()
    print("set ARENA_GRID_MODE=construction|formal", file=sys.stderr)
    return 64


if __name__ == "__main__":
    raise SystemExit(main())
