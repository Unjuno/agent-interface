from __future__ import annotations

import base64
import binascii
import hashlib
import json
import math
import statistics
from pathlib import Path
from typing import Any

from engine import HEIGHT, WIDTH, BenchmarkSession, EpisodeSpec, StageSpec, generate_episode
from renderer import render_base
from runner import ALLOCATION, ARMS, DIFFICULTY, FORMAL_SEEDS, MODEL, MODEL_DIGEST, source_pixel_proposal


def expected_scene(seed: int) -> tuple[BenchmarkSession, dict[str, Any]]:
    episode = generate_episode(seed, DIFFICULTY)
    stage = next(item for item in episode.stages if item.kind == "target")
    session = BenchmarkSession(EpisodeSpec(episode.schema, seed, episode.difficulty,
                                           (StageSpec("target", stage.payload),)))
    target = session._object_by_id(session.stage.payload["target_id"])
    return session, {"instruction": session.instruction(),
                     "target": {"color": target.color, "shape": target.shape, "center_x": target.x,
                                "center_y": target.y, "radius": target.radius},
                     "objects": [{"color": obj.color, "shape": obj.shape, "center_x": obj.x,
                                  "center_y": obj.y, "radius": obj.radius} for obj in session.objects],
                     "seed": seed, "difficulty": DIFFICULTY}


def _prompt(instruction: str, arm: str) -> str:
    from runner import prompt_for
    return prompt_for(instruction, arm)


def _call_errors(record: dict[str, Any], case: Path, seed: int, arm: str,
                 order: int, prompt: str) -> list[str]:
    errors = []
    if record.get("schema") != "arena-v0-coordinate-scale-call-v1" or record.get("difficulty") != DIFFICULTY:
        errors.append("record_schema_or_difficulty")
    if record.get("seed") != seed or record.get("arm") != arm or record.get("order") != order:
        errors.append("call_identity")
    if record.get("model") != MODEL or record.get("model_digest") != MODEL_DIGEST:
        errors.append("model_identity")
    if record.get("prompt") != prompt:
        errors.append("prompt_mismatch")
    body = record.get("request", {})
    if body.get("model") != MODEL or body.get("prompt") != prompt or body.get("stream") is not False:
        errors.append("request_contract")
    if body.get("format", {}).get("type") != "object":
        errors.append("request_output_schema")
    options = body.get("options", {})
    if options.get("temperature") != 0 or options.get("seed") != 424242 or options.get("num_predict") != 128:
        errors.append("decode_settings")
    if record.get("image_path") != "raw.png":
        errors.append("image_path_identity")
    image_path = case / "raw.png"
    if not image_path.is_file():
        return errors + ["image_missing"]
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
    if not isinstance(proposal, dict) or not all(key in proposal for key in ("color", "shape", "x", "y")):
        errors.append("proposal_schema")
    elif any(isinstance(proposal[key], bool) or not isinstance(proposal[key], (int, float))
             or not math.isfinite(proposal[key]) for key in ("x", "y")):
        errors.append("proposal_coordinates")
    try:
        response = record.get("response", {})
        if response.get("model") != MODEL:
            errors.append("raw_response_model")
        if json.loads(response.get("response", "")) != proposal:
            errors.append("response_proposal_binding")
    except (json.JSONDecodeError, AttributeError, TypeError):
        errors.append("raw_response_json")
    expected_mapped = source_pixel_proposal(proposal, arm)
    if record.get("source_pixel_proposal") != expected_mapped:
        errors.append("source_pixel_mapping")
    wall = record.get("wall_seconds")
    if not isinstance(wall, (int, float)) or not math.isfinite(wall) or wall <= 0:
        errors.append("request_latency")
    return errors


def _in_bounds(proposal: dict[str, Any], arm: str) -> bool:
    maximum_x, maximum_y = (1, 1) if arm == "NORM01" else (WIDTH - 1, HEIGHT - 1)
    return 0 <= proposal["x"] <= maximum_x and 0 <= proposal["y"] <= maximum_y


def audit_pair(case: Path, seed: int) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    expected, truth = expected_scene(seed)
    image, rendered_truth = render_base(seed, DIFFICULTY)
    if not (case / "truth.json").is_file() or json.loads((case / "truth.json").read_text()) != rendered_truth:
        errors.append("seed_truth_binding")
    if not (case / "raw.png").is_file() or (case / "raw.png").read_bytes() != image:
        errors.append("stimulus_reconstruction")
    records = {}
    index = FORMAL_SEEDS.index(seed)
    order_arms = ARMS if index % 2 == 0 else tuple(reversed(ARMS))
    for order, arm in enumerate(order_arms):
        path = case / f"{arm.lower()}-call.json"
        if not path.is_file():
            errors.append(f"{arm}:call_missing")
            continue
        record = json.loads(path.read_text(encoding="utf-8"))
        records[arm] = record
        errors.extend(f"{arm}:{error}" for error in _call_errors(record, case, seed, arm, order,
                                                                  _prompt(truth["instruction"], arm)))
    if len(records) != 2:
        return None, errors + ["pair_incomplete"]
    if records["PIXEL"].get("image_sha256") != records["NORM01"].get("image_sha256"):
        errors.append("paired_image_mismatch")
    target = truth["target"]
    target_object = next(obj for obj in expected.objects
                         if obj.color == target["color"] and obj.shape == target["shape"])
    scored = {}
    for arm, record in records.items():
        proposal = record.get("proposal") or {}
        mapped = record.get("source_pixel_proposal") or {}
        exact = proposal.get("color") == target["color"] and proposal.get("shape") == target["shape"]
        try:
            x, y = float(mapped["x"]), float(mapped["y"])
            hit_obj = expected._object_at(x, y)
            hit = hit_obj is not None and hit_obj.object_id == target_object.object_id
            error = math.hypot(x - target["center_x"], y - target["center_y"])
        except (KeyError, TypeError, ValueError):
            hit, error = False, None
        in_bounds = _in_bounds(proposal, arm) if all(isinstance(proposal.get(k), (int, float))
                                                     and not isinstance(proposal.get(k), bool) for k in ("x", "y")) else False
        scored[arm] = {"exact_target": exact, "engine_hit": hit, "in_bounds": in_bounds,
                       "center_error_px": error, "proposal": proposal,
                       "source_pixel_proposal": mapped, "wall_seconds": record.get("wall_seconds")}
    return {"seed": seed, **scored}, errors


def audit_tree(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    results = []
    state_path = root / "RUN_STATE.json"
    freeze_path = Path(__file__).resolve().parent / "FREEZE.json"
    if not state_path.is_file():
        errors.append("run_state_missing")
    else:
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("status") != "CAPTURED" or state.get("calls_completed") != 24:
            errors.append("run_state_incomplete")
        if state.get("allocation") != ALLOCATION:
            errors.append("run_state_allocation")
        if state.get("model", {}).get("name") != MODEL or state.get("model", {}).get("digest") != MODEL_DIGEST:
            errors.append("run_state_model")
        if not freeze_path.is_file():
            errors.append("freeze_missing")
        else:
            freeze_bytes = freeze_path.read_bytes()
            freeze = json.loads(freeze_bytes)
            if hashlib.sha256(freeze_bytes).hexdigest() != state.get("freeze_sha256"):
                errors.append("freeze_hash")
            if freeze.get("allocation") != ALLOCATION or freeze.get("model", {}).get("digest") != MODEL_DIGEST:
                errors.append("freeze_identity")
            if freeze.get("container", {}).get("image_id") != state.get("container_image_id"):
                errors.append("freeze_container_image")
            for relative, expected_hash in freeze.get("source_hashes", {}).items():
                frozen_path = freeze_path.parents[3] / relative
                if not frozen_path.is_file() or hashlib.sha256(frozen_path.read_bytes()).hexdigest() != expected_hash:
                    errors.append(f"frozen_source:{relative}")
    for seed in FORMAL_SEEDS:
        case = root / "calls" / f"case-{FORMAL_SEEDS.index(seed) + 1:02d}-{seed}"
        result, pair_errors = audit_pair(case, seed)
        errors.extend(f"seed={seed}:{error}" for error in pair_errors)
        if result is not None:
            results.append(result)
    if len(results) != len(FORMAL_SEEDS):
        errors.append("pair_count")
    summary = {}
    for arm in ARMS:
        values = [row[arm] for row in results if row[arm]["center_error_px"] is not None]
        summary[arm] = {
            "pairs_scored": len(values),
            "in_bounds": sum(value["in_bounds"] for value in values),
            "exact_target": sum(value["exact_target"] for value in values),
            "engine_hit": sum(value["engine_hit"] for value in values),
            "median_center_error_px": None if not values else statistics.median(value["center_error_px"] for value in values),
            "mean_model_wall_seconds": None if not values else sum(value["wall_seconds"] for value in values) / len(values),
        }
    pairwise_wins = sum(row["NORM01"]["center_error_px"] is not None
                        and row["PIXEL"]["center_error_px"] is not None
                        and row["NORM01"]["center_error_px"] < row["PIXEL"]["center_error_px"]
                        for row in results)
    pixel, normalized = summary["PIXEL"], summary["NORM01"]
    gate = (len(results) == 12 and not errors and normalized["in_bounds"] >= 10
            and normalized["exact_target"] >= pixel["exact_target"]
            and normalized["engine_hit"] >= pixel["engine_hit"]
            and normalized["median_center_error_px"] is not None
            and pixel["median_center_error_px"] is not None
            and normalized["median_center_error_px"] <= 0.8 * pixel["median_center_error_px"]
            and pairwise_wins >= 8)
    disposition = ("STOP_AUDIT_INTEGRITY_FAILURE" if errors else
                   "PASS_NORMALIZED_COORDINATE_SIGNAL_SCOPED" if gate else "HOLD_NO_PREREGISTERED_GAIN")
    return {"schema": "arena-v0-coordinate-scale-audit-v1", "allocation": ALLOCATION,
            "disposition": disposition, "errors": errors, "pairs": results,
            "summary": summary, "normalized_pairwise_center_error_wins": pairwise_wins,
            "formal_claim_scope": "static target localization proposal; no GUI input or task-effect claim"}


def main() -> int:
    import sys
    if len(sys.argv) != 2:
        print("usage: audit.py /evidence/formal/001", file=sys.stderr)
        return 64
    result = audit_tree(Path(sys.argv[1]))
    print(json.dumps(result, sort_keys=True))
    return 2 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
