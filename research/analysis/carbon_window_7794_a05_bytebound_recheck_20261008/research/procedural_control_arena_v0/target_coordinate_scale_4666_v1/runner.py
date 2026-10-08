from __future__ import annotations

import base64
import hashlib
import json
import os
import platform
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from engine import HEIGHT, WIDTH
from renderer import render_base


MODEL = "qwen2.5vl:7b"
MODEL_DIGEST = "5ced39dfa4bac325dc183dd1e4febaa1c46b3ea28bce48896c8e69c1e79611cc"
API = "http://host.docker.internal:11434"
IMAGE_ID = "sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e"
ALLOCATION = "arena-v0-coordinate-scale-4666-v1-20260928-01"
DIFFICULTY = 0.35
CONSTRUCTION_SEED = 8866620
FORMAL_SEEDS = tuple(range(8866621, 8866633))
ARMS = ("PIXEL", "NORM01")
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]


def http_json(url: str, payload: dict[str, Any] | None = None, *, timeout: float = 180) -> tuple[dict[str, Any], float]:
    data = None if payload is None else json.dumps(payload, separators=(",", ":")).encode()
    request = urllib.request.Request(url, data=data,
                                    headers={"Content-Type": "application/json"} if data else {})
    start = time.monotonic_ns()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        result = json.loads(response.read())
    return result, (time.monotonic_ns() - start) / 1e9


def verify_model() -> dict[str, Any]:
    tags, _ = http_json(f"{API}/api/tags", timeout=5)
    matches = [row for row in tags.get("models", []) if row.get("name") == MODEL]
    if len(matches) != 1 or matches[0].get("digest") != MODEL_DIGEST:
        raise RuntimeError(f"STOP_MODEL_DIGEST_MISMATCH: {matches}")
    return {"name": MODEL, "digest": matches[0]["digest"], "size": matches[0].get("size")}


def verify_freeze() -> dict[str, Any]:
    path = HERE / "FREEZE.json"
    if not path.is_file():
        raise RuntimeError("STOP_FREEZE_MISSING")
    freeze = json.loads(path.read_text(encoding="utf-8"))
    if freeze.get("allocation") != ALLOCATION or freeze.get("formal_seeds") != list(FORMAL_SEEDS):
        raise RuntimeError("STOP_FREEZE_ALLOCATION_MISMATCH")
    if freeze.get("model", {}).get("digest") != MODEL_DIGEST:
        raise RuntimeError("STOP_FREEZE_MODEL_MISMATCH")
    if freeze.get("container", {}).get("image_id") != os.environ.get("EXPERIMENT_IMAGE_ID"):
        raise RuntimeError("STOP_CONTAINER_IMAGE_MISMATCH")
    if platform.machine().lower() not in {"arm64", "aarch64"}:
        raise RuntimeError(f"STOP_CONTAINER_ARCH_MISMATCH: {platform.machine()}")
    for relative, expected in freeze.get("source_hashes", {}).items():
        path = REPO_ROOT / relative
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"STOP_FROZEN_SOURCE_MISMATCH: {relative}")
    return freeze


def prompt_for(instruction: str, arm: str) -> str:
    wanted = instruction.removeprefix("TARGET: ").removeprefix("click the ").removesuffix(".")
    common = (f"Locate the object described as {wanted}. Return its visual center. "
              "Return JSON only with keys color, shape, x, y; color and shape must identify the object.")
    if arm == "PIXEL":
        return common + (f" x and y are source-image pixel coordinates in a {WIDTH} by {HEIGHT} image, "
                         f"with origin at top left (x=0..{WIDTH - 1}, y=0..{HEIGHT - 1}).")
    if arm == "NORM01":
        return common + (" x and y are normalized source-image coordinates from 0 to 1 inclusive: "
                         "x=0 is the left edge, x=1 the right edge, y=0 the top edge, and y=1 the bottom edge.")
    raise ValueError(f"unknown arm: {arm}")


def source_pixel_proposal(proposal: Any, arm: str) -> dict[str, Any] | None:
    if not isinstance(proposal, dict):
        return None
    x, y = proposal.get("x"), proposal.get("y")
    if isinstance(x, bool) or isinstance(y, bool) or not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
        return None
    if arm == "NORM01":
        x, y = x * (WIDTH - 1), y * (HEIGHT - 1)
    return {"color": proposal.get("color"), "shape": proposal.get("shape"), "x": x, "y": y}


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
        proposal, parse_error = json.loads(raw), None
    except (json.JSONDecodeError, TypeError) as exc:
        proposal, parse_error = None, f"{type(exc).__name__}: {exc}"
    record = {"schema": "arena-v0-coordinate-scale-call-v1", "seed": seed,
              "difficulty": DIFFICULTY, "arm": arm, "order": order,
              "model": response.get("model"), "model_digest": MODEL_DIGEST,
              "prompt": prompt, "image_path": image_path.name,
              "image_sha256": hashlib.sha256(image).hexdigest(),
              "request_sha256": hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
              "request": body, "response": response, "wall_seconds": wall_seconds,
              "proposal": proposal, "source_pixel_proposal": source_pixel_proposal(proposal, arm),
              "parse_error": parse_error, "recorded_utc": datetime.now(timezone.utc).isoformat()}
    out.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")
    return record


def make_stimulus(directory: Path, seed: int) -> dict[str, Any]:
    directory.mkdir(parents=True, exist_ok=True)
    image, truth = render_base(seed, DIFFICULTY)
    (directory / "raw.png").write_bytes(image)
    (directory / "truth.json").write_text(json.dumps(truth, sort_keys=True) + "\n", encoding="utf-8")
    return truth


def construction() -> int:
    out = HERE / "construction" / f"seed-{CONSTRUCTION_SEED}"
    if out.exists():
        raise SystemExit("STOP_CONSTRUCTION_OUTPUT_EXISTS; do not overwrite or retry")
    verify_freeze()
    model = verify_model()
    truth = make_stimulus(out, CONSTRUCTION_SEED)
    records = {}
    for order, arm in enumerate(ARMS):
        records[arm] = one_request(CONSTRUCTION_SEED, arm, out / "raw.png",
                                   prompt_for(truth["instruction"], arm),
                                   out / f"{arm.lower()}-call.json", order)
    result = {"status": "CONSTRUCTION_ONLY", "allocation": ALLOCATION,
              "seed": CONSTRUCTION_SEED, "model": model,
              "proposals": {arm: records[arm]["proposal"] for arm in ARMS},
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
    state: dict[str, Any] = {"status": "RUNNING", "allocation": ALLOCATION,
                             "started_utc": datetime.now(timezone.utc).isoformat(), "model": model,
                             "freeze_sha256": hashlib.sha256((HERE / "FREEZE.json").read_bytes()).hexdigest(),
                             "container_image_id": freeze["container"]["image_id"], "calls_completed": 0}
    (out / "RUN_STATE.json").write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        warm_dir = out / "warmup"
        truth = make_stimulus(warm_dir, CONSTRUCTION_SEED)
        warm = one_request(CONSTRUCTION_SEED, "PIXEL", warm_dir / "raw.png",
                           prompt_for(truth["instruction"], "PIXEL"), warm_dir / "warmup-call.json", 0)
        state["warmup_parse_error"] = warm["parse_error"]
        (warm_dir / "truth.json").write_text(json.dumps(truth, sort_keys=True) + "\n", encoding="utf-8")
        if warm["parse_error"]:
            raise RuntimeError("STOP_WARMUP_OUTPUT_INVALID")
        for pair_index, seed in enumerate(FORMAL_SEEDS):
            case = out / "calls" / f"case-{pair_index + 1:02d}-{seed}"
            truth = make_stimulus(case, seed)
            prompt = {arm: prompt_for(truth["instruction"], arm) for arm in ARMS}
            order_arms = ARMS if pair_index % 2 == 0 else tuple(reversed(ARMS))
            for order, arm in enumerate(order_arms):
                record = one_request(seed, arm, case / "raw.png", prompt[arm],
                                     case / f"{arm.lower()}-call.json", order)
                state["calls_completed"] += 1
                (out / "RUN_STATE.json").write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                if record["parse_error"]:
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
    mode = os.environ.get("COORDINATE_SCALE_MODE")
    if mode == "construction":
        return construction()
    if mode == "formal":
        return formal()
    print("set COORDINATE_SCALE_MODE=construction|formal", file=sys.stderr)
    return 64


if __name__ == "__main__":
    raise SystemExit(main())
