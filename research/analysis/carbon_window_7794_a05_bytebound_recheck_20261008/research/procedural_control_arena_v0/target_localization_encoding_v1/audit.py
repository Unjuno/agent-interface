from __future__ import annotations

import base64
import binascii
import hashlib
import json
import math
import statistics
from pathlib import Path
from typing import Any

from engine import BenchmarkSession, EpisodeSpec, StageSpec, generate_episode
from renderer import render_pair


MODEL = "qwen2.5vl:7b"
MODEL_DIGEST = "5ced39dfa4bac325dc183dd1e4febaa1c46b3ea28bce48896c8e69c1e79611cc"
SEEDS = tuple(range(8866601, 8866613))
DIFFICULTY = 0.35


def median_center_error(values: list[float]) -> float | None:
    return None if not values else statistics.median(values)


def expected_scene(seed: int) -> tuple[BenchmarkSession, dict[str, Any]]:
    episode = generate_episode(seed, DIFFICULTY)
    target_stage = next(item for item in episode.stages if item.kind == "target")
    spec = EpisodeSpec(episode.schema, seed, episode.difficulty, (StageSpec("target", target_stage.payload),))
    session = BenchmarkSession(spec)
    target = session._object_by_id(session.stage.payload["target_id"])
    return session, {"instruction": session.instruction(),
                     "target": {"color": target.color, "shape": target.shape, "center_x": target.x,
                                "center_y": target.y, "radius": target.radius},
                     "objects": [{"color": obj.color, "shape": obj.shape, "center_x": obj.x,
                                  "center_y": obj.y, "radius": obj.radius} for obj in session.objects],
                     "seed": seed, "difficulty": DIFFICULTY}


def _call_errors(record: dict[str, Any], root: Path, seed: int, arm: str, order: int,
                 prompt: str) -> list[str]:
    errors = []
    if record.get("seed") != seed or record.get("arm") != arm or record.get("order") != order:
        errors.append("call_identity")
    if record.get("model") != MODEL or record.get("model_digest") != MODEL_DIGEST:
        errors.append("model_identity")
    if record.get("prompt") != prompt:
        errors.append("prompt_mismatch")
    body = record.get("request", {})
    if body.get("model") != MODEL or body.get("prompt") != prompt:
        errors.append("request_contract")
    if record.get("schema") != "arena-v0-grid-localization-call-v1" or record.get("difficulty") != DIFFICULTY:
        errors.append("record_schema_or_difficulty")
    if record.get("image_path") != ("raw.png" if arm == "RAW" else "grid80.png"):
        errors.append("image_path_identity")
    if body.get("stream") is not False or body.get("format", {}).get("type") != "object":
        errors.append("request_generation_contract")
    opts = body.get("options", {})
    if opts.get("temperature") != 0 or opts.get("seed") != 424242 or opts.get("num_predict") != 128:
        errors.append("decode_settings")
    image_path = root / record.get("image_path", "")
    if not image_path.is_file():
        errors.append("image_missing")
        return errors
    image = image_path.read_bytes()
    if hashlib.sha256(image).hexdigest() != record.get("image_sha256"):
        errors.append("image_hash")
    images = body.get("images", [])
    if len(images) != 1:
        errors.append("request_image_count")
    else:
        try:
            if base64.b64decode(images[0], validate=True) != image:
                errors.append("request_image_binding")
        except (binascii.Error, ValueError):
            errors.append("request_image_encoding")
    request_hash = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if request_hash != record.get("request_sha256"):
        errors.append("request_hash")
    proposal = record.get("proposal")
    if not isinstance(proposal, dict) or not all(k in proposal for k in ("color", "shape", "x", "y")):
        errors.append("proposal_schema")
    elif not all(isinstance(proposal[k], (int, float)) and math.isfinite(proposal[k]) for k in ("x", "y")):
        errors.append("proposal_coordinate")
    try:
        response = record.get("response", {})
        if response.get("model") != MODEL:
            errors.append("raw_response_model_identity")
        if json.loads(response.get("response", "")) != proposal:
            errors.append("response_proposal_binding")
    except (json.JSONDecodeError, AttributeError, TypeError):
        errors.append("raw_response_json")
    wall = record.get("wall_seconds")
    if not isinstance(wall, (int, float)) or not math.isfinite(wall) or wall <= 0:
        errors.append("request_latency")
    return errors


def audit_pair(case_dir: Path, seed: int) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    expected, truth = expected_scene(seed)
    raw_image, grid_image, rendered_truth = render_pair(seed, DIFFICULTY)
    truth_path = case_dir / "truth.json"
    if not truth_path.is_file():
        return None, ["truth_missing"]
    observed_truth = json.loads(truth_path.read_text(encoding="utf-8"))
    if observed_truth != rendered_truth or observed_truth != {**truth, "objects": truth["objects"]}:
        errors.append("seed_truth_binding")
    raw_path, grid_path = case_dir / "raw.png", case_dir / "grid80.png"
    if not raw_path.is_file() or not grid_path.is_file() or raw_path.read_bytes() != raw_image or grid_path.read_bytes() != grid_image:
        errors.append("stimulus_reconstruction")
    raw_record_path, grid_record_path = case_dir / "raw-call.json", case_dir / "grid80-call.json"
    if not raw_record_path.is_file() or not grid_record_path.is_file():
        return None, errors + ["pair_incomplete"]
    records = {"RAW": json.loads(raw_record_path.read_text(encoding="utf-8")),
               "GRID80": json.loads(grid_record_path.read_text(encoding="utf-8"))}
    case_index = SEEDS.index(seed)
    expected_arms = ("RAW", "GRID80") if case_index % 2 == 0 else ("GRID80", "RAW")
    prompt = (f"Locate the object described as {truth['instruction'].removeprefix('TARGET: ').removeprefix('click the ').removesuffix('.')}. "
              "Return the object's visual center in SOURCE-image pixel coordinates. The image is 640 pixels wide and 480 pixels high; "
              "origin (0,0) is the top-left. Return JSON only with keys color, shape, x, y. x and y must be numbers.")
    for order, arm in enumerate(expected_arms):
        errors.extend(f"{arm}:{e}" for e in _call_errors(records[arm], case_dir, seed, arm, order, prompt))
    if records["RAW"].get("prompt") != records["GRID80"].get("prompt"):
        errors.append("paired_prompt_mismatch")
    if records["RAW"].get("image_sha256") == records["GRID80"].get("image_sha256"):
        errors.append("treatment_not_distinct")
    target = truth["target"]
    target_obj = next(obj for obj in expected.objects if obj.color == target["color"] and obj.shape == target["shape"])
    scored = {}
    for arm, record in records.items():
        p = record.get("proposal") or {}
        exact = p.get("color") == target["color"] and p.get("shape") == target["shape"]
        try:
            hit_obj = expected._object_at(float(p["x"]), float(p["y"]))
            hit = hit_obj is not None and hit_obj.object_id == target_obj.object_id
            error_px = math.hypot(float(p["x"]) - target["center_x"], float(p["y"]) - target["center_y"])
        except (KeyError, TypeError, ValueError):
            hit, error_px = False, None
        scored[arm] = {"exact_target": exact, "engine_hit": hit, "center_error_px": error_px,
                       "wall_seconds": record.get("wall_seconds"), "proposal": p}
    return {"seed": seed, **scored}, errors


def audit_tree(root: Path) -> dict[str, Any]:
    errors = []
    results = []
    freeze_path = Path(__file__).resolve().parent / "FREEZE.json"
    state_path = root / "RUN_STATE.json"
    if not state_path.is_file():
        errors.append("run_state_missing")
    else:
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("status") != "CAPTURED" or state.get("calls_completed") != 24:
            errors.append("run_state_incomplete")
        if state.get("model", {}).get("name") != MODEL or state.get("model", {}).get("digest") != MODEL_DIGEST:
            errors.append("run_state_model")
        if not freeze_path.is_file():
            errors.append("freeze_missing")
        else:
            freeze_bytes = freeze_path.read_bytes()
            freeze = json.loads(freeze_bytes)
            if hashlib.sha256(freeze_bytes).hexdigest() != state.get("freeze_sha256"):
                errors.append("freeze_hash")
            if freeze.get("model", {}).get("digest") != MODEL_DIGEST:
                errors.append("freeze_model")
            if freeze.get("container", {}).get("image_id") != state.get("container_image_id"):
                errors.append("freeze_container_image")
            for relative, expected_hash in freeze.get("source_hashes", {}).items():
                frozen_path = freeze_path.parents[3] / relative
                if not frozen_path.is_file() or hashlib.sha256(frozen_path.read_bytes()).hexdigest() != expected_hash:
                    errors.append(f"frozen_source:{relative}")
    for seed in SEEDS:
        case = root / "calls" / f"case-{SEEDS.index(seed) + 1:02d}-{seed}"
        result, case_errors = audit_pair(case, seed)
        errors.extend(f"seed={seed}:{e}" for e in case_errors)
        if result is not None:
            results.append(result)
    if len(results) != len(SEEDS):
        errors.append("pair_count")
    by_arm = {}
    for arm in ("RAW", "GRID80"):
        values = [row[arm] for row in results if row[arm]["center_error_px"] is not None]
        median = median_center_error([v["center_error_px"] for v in values])
        by_arm[arm] = {"pairs_scored": len(values), "exact_target": sum(v["exact_target"] for v in values),
                       "engine_hit": sum(v["engine_hit"] for v in values), "median_center_error_px": median,
                       "mean_model_wall_seconds": None if not values else sum(v["wall_seconds"] for v in values) / len(values)}
    pairwise_improvement = sum(
        row["GRID80"]["center_error_px"] is not None and row["RAW"]["center_error_px"] is not None
        and row["GRID80"]["center_error_px"] < row["RAW"]["center_error_px"] for row in results)
    raw, grid = by_arm["RAW"], by_arm["GRID80"]
    gate = (len(results) == 12 and not errors and grid["exact_target"] >= raw["exact_target"]
            and grid["engine_hit"] >= raw["engine_hit"] and grid["median_center_error_px"] is not None
            and raw["median_center_error_px"] is not None and grid["median_center_error_px"] <= 0.8 * raw["median_center_error_px"]
            and pairwise_improvement >= 8)
    return {"schema": "arena-v0-grid-localization-audit-v1", "disposition":
            "PASS_GRID80_LOCALIZATION_SIGNAL_SCOPED" if gate else "HOLD_NO_PREREGISTERED_GAIN",
            "errors": errors, "pairs": results, "summary": by_arm,
            "grid80_pairwise_center_error_wins": pairwise_improvement,
            "formal_claim_scope": "static target-only localization proposals; no GUI inputs or action-performance claim"}


def main() -> int:
    import sys
    if len(sys.argv) != 2:
        print("usage: audit.py /evidence/formal/001", file=sys.stderr)
        return 64
    result = audit_tree(Path(sys.argv[1]))
    print(json.dumps(result, sort_keys=True))
    return 0 if not result["errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
