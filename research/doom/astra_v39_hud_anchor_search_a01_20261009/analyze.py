"""Evaluate exact WAD glyph matching with a bounded anchor-offset search."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import io
import json
import math
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance


PACKAGE = Path(__file__).resolve().parent
FREEZE = json.loads((PACKAGE / "FREEZE.json").read_text(encoding="utf-8"))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob(repo: Path, commit: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=repo)


def rgb_digest(image: Image.Image) -> str:
    image = image.convert("RGB")
    width, height = image.size
    return sha(width.to_bytes(4, "big") + height.to_bytes(4, "big") + image.tobytes())


def variants(source: Image.Image):
    yield "baseline", {}, source.copy()
    for dx, dy in FREEZE["translation_px"]:
        shifted = Image.new("RGB", source.size, (0, 0, 0))
        shifted.paste(source, (dx, dy))
        yield f"translate_{dx:+d}_{dy:+d}", {"dx": dx, "dy": dy}, shifted
    for factor in FREEZE["brightness_factors"]:
        yield f"brightness_{factor:.2f}", {"factor": factor}, ImageEnhance.Brightness(source).enhance(factor)
    for factor in FREEZE["contrast_factors"]:
        yield f"contrast_{factor:.2f}", {"factor": factor}, ImageEnhance.Contrast(source).enhance(factor)
    for quality in FREEZE["jpeg_qualities"]:
        output = io.BytesIO()
        source.save(output, format="JPEG", quality=quality, subsampling=0, optimize=False)
        encoded = output.getvalue()
        with Image.open(io.BytesIO(encoded)) as reopened:
            yield f"jpeg_q{quality}", {"quality": quality, "jpeg_sha256": sha(encoded)}, reopened.convert("RGB")


def percentile_stats(values: list[int]) -> dict:
    ordered = sorted(values)
    return {
        "n": len(ordered),
        "median_ns": statistics.median(ordered),
        "p95_nearest_rank_ns": ordered[math.ceil(0.95 * len(ordered)) - 1],
        "max_ns": max(ordered),
    }


def classify_offset(reader, image: Image.Image, observation: dict, dx: int, dy: int):
    geometry = observation["pointer_binding"]["geometry"]
    left = geometry[0] + reader.local_anchor[0] + dx
    top = geometry[1] + reader.local_anchor[1] + dy
    width, height = reader.glyph_size
    if left < 0 or top < 0 or left + width * reader.slots > image.width or top + height > image.height:
        return None
    number = np.asarray(image.convert("RGB").crop((left, top, left + width * reader.slots, top + height)))
    digits, slots = [], []
    for slot_index in range(reader.slots):
        crop = number[:, slot_index * width:(slot_index + 1) * width]
        scores = [float(np.all(crop == template, axis=2)[mask].mean()) for template, mask in reader.templates]
        order = sorted(range(10), key=scores.__getitem__, reverse=True)
        best, second = order[:2]
        if scores[best] < reader.minimum_score or scores[best] - scores[second] < reader.minimum_margin:
            return None
        digits.append(best)
        slots.append({"slot": slot_index, "digit": best, "best_score": scores[best], "second_score": scores[second]})
    first = next((index for index, digit in enumerate(digits) if digit is not None), None)
    if first is None or any(digit is None for digit in digits[first:]) or any(digit is not None for digit in digits[:first]):
        return None
    value = int("".join(str(digit) for digit in digits[first:]))
    return {"dx": dx, "dy": dy, "value": value, "mean_score": statistics.mean(slot["best_score"] for slot in slots), "slots": slots}


def anchor_search(reader, observation: dict, image: Image.Image) -> dict:
    matches = []
    radius = FREEZE["anchor_search_radius_px"]
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            match = classify_offset(reader, image, observation, dx, dy)
            if match is not None:
                matches.append(match)
    values = sorted({match["value"] for match in matches})
    if not values:
        return {"status": "unknown", "value": None, "reason": "no_complete_anchor_match", "candidate_values": [], "matching_offset_count": 0}
    if len(values) > 1:
        return {"status": "unknown", "value": None, "reason": "conflicting_anchor_values", "candidate_values": values,
                "matching_offset_count": len(matches)}
    chosen = max(matches, key=lambda match: (match["mean_score"], -(abs(match["dx"]) + abs(match["dy"])), -abs(match["dy"]), -abs(match["dx"])))
    return {
        "status": "observed", "value": values[0], "reason": None, "candidate_values": values,
        "chosen_offset": {"dx": chosen["dx"], "dy": chosen["dy"]},
        "matching_offset_count": len(matches), "minimum_glyph_score": min(slot["best_score"] for slot in chosen["slots"]),
    }


def blank_health_roi(image: Image.Image, binding: dict) -> Image.Image:
    blank = image.convert("RGB").copy()
    x, y, _, _ = binding["geometry"]
    local_x, local_y = FREEZE["health_local_anchor"]
    width, height = FREEZE["glyph_size"]
    draw = ImageDraw.Draw(blank)
    draw.rectangle((x + local_x, y + local_y, x + local_x + width * FREEZE["slots"] - 1,
                    y + local_y + height - 1), fill=(0, 0, 0))
    return blank


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wad", type=Path, required=True)
    parser.add_argument("--git-root", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    repo = args.git_root.resolve()
    if sha(Path(__file__).read_bytes()) != FREEZE["candidate_sha256"] or sha((PACKAGE / "audit.py").read_bytes()) != FREEZE["auditor_sha256"]:
        raise SystemExit("HOLD_CODE_HASH")
    wad_bytes = args.wad.resolve().read_bytes()
    if sha(wad_bytes) != FREEZE["wad_sha256"]:
        raise SystemExit("HOLD_WAD_HASH")
    if sys.version.split()[0] != FREEZE["runtime_versions"]["python"] or __import__("PIL").__version__ != FREEZE["runtime_versions"]["pillow"] or np.__version__ != FREEZE["runtime_versions"]["numpy"]:
        raise SystemExit("HOLD_RUNTIME_VERSION")

    base = FREEZE["base_commit"]
    evidence_commit = FREEZE["evidence_commit"]
    source_freeze_bytes = git_blob(repo, base, FREEZE["source_freeze_path"])
    prior_freeze_bytes = git_blob(repo, evidence_commit, FREEZE["prior_freeze_path"])
    prior_result_bytes = git_blob(repo, evidence_commit, FREEZE["prior_result_path"])
    if sha(source_freeze_bytes) != FREEZE["source_freeze_sha256"] or sha(prior_freeze_bytes) != FREEZE["prior_freeze_sha256"] or sha(prior_result_bytes) != FREEZE["prior_result_sha256"]:
        raise SystemExit("HOLD_PRIOR_EVIDENCE_HASH")
    source_freeze = json.loads(source_freeze_bytes)
    prior_freeze = json.loads(prior_freeze_bytes)
    prior_result = json.loads(prior_result_bytes)
    if prior_result["status"] != "PASS_NO_FALSE_OBSERVED_VALUE" or prior_result["perturbed_reads"] != 182:
        raise SystemExit("HOLD_PRIOR_RESULT")
    for path, expected in FREEZE["source_blobs"].items():
        actual = subprocess.check_output(["git", "rev-parse", f"{base}:{path}"], cwd=repo, text=True).strip()
        if actual != expected:
            raise SystemExit(f"HOLD_SOURCE_BLOB:{path}")

    with tempfile.TemporaryDirectory(prefix="v39-anchor-search-") as temp:
        module_root = Path(temp)
        for path in FREEZE["reader_modules"]:
            (module_root / Path(path).name).write_bytes(git_blob(repo, base, path))
        sys.path.insert(0, str(module_root))
        module = importlib.import_module("doom_hud_signal_v3")
        reader = module.DoomStatusNumberReader(args.wad, signal_id="health")
        rows = []
        blank_rows = []
        frame_info = source_freeze["frames"]
        for frame in frame_info:
            png = git_blob(repo, base, frame["frame_path"])
            if sha(png) != frame["sha256"]:
                raise SystemExit(f"HOLD_FRAME_HASH:{frame['frame_path']}")
            with Image.open(io.BytesIO(png)) as opened:
                original = opened.convert("RGB")
            observation = {"sequence": frame["sequence"], "capture_ns": frame["capture_ns"], "pointer_binding": frame["pointer_binding"]}
            for variant, parameters, image in variants(original):
                baseline_start = time.perf_counter_ns()
                exact = reader.read_frame(observation, image)
                baseline_ns = time.perf_counter_ns() - baseline_start
                candidate_start = time.perf_counter_ns()
                candidate = anchor_search(reader, observation, image)
                candidate_ns = time.perf_counter_ns() - candidate_start
                rows.append({
                    "frame_index": frame["index"], "source_path": frame["frame_path"], "source_png_sha256": frame["sha256"],
                    "sequence": frame["sequence"], "capture_ns": frame["capture_ns"], "pointer_binding": frame["pointer_binding"],
                    "expected_health": source_freeze["manual_health"][frame["index"]], "variant": variant, "parameters": parameters,
                    "transformed_rgb_sha256": rgb_digest(image), "exact_status": exact.get("status"), "exact_value": exact.get("value"),
                    "exact_elapsed_ns": baseline_ns, "candidate_status": candidate["status"], "candidate_value": candidate["value"],
                    "candidate_reason": candidate["reason"], "candidate_values": candidate["candidate_values"],
                    "chosen_offset": candidate.get("chosen_offset"), "matching_offset_count": candidate["matching_offset_count"],
                    "candidate_elapsed_ns": candidate_ns,
                })
            blank = blank_health_roi(original, frame["pointer_binding"])
            started = time.perf_counter_ns()
            blank_result = anchor_search(reader, observation, blank)
            elapsed = time.perf_counter_ns() - started
            blank_rows.append({"frame_index": frame["index"], "sequence": frame["sequence"], "transformed_rgb_sha256": rgb_digest(blank),
                               "status": blank_result["status"], "value": blank_result["value"], "reason": blank_result["reason"], "elapsed_ns": elapsed})

    baseline = [row for row in rows if row["variant"] == "baseline"]
    translated = [row for row in rows if row["variant"].startswith("translate_")]
    perturbed = [row for row in rows if row["variant"] != "baseline"]
    wrong = [row for row in perturbed if row["candidate_status"] == "observed" and row["candidate_value"] != row["expected_health"]]
    exact_times = [row["exact_elapsed_ns"] for row in rows]
    candidate_times = [row["candidate_elapsed_ns"] for row in rows]
    exact_stats = percentile_stats(exact_times)
    candidate_stats = percentile_stats(candidate_times)
    status = "PASS_BOUNDED_ANCHOR_SEARCH" if (
        len(baseline) == 13 and all(row["candidate_status"] == "observed" and row["candidate_value"] == row["expected_health"] for row in baseline)
        and len(translated) == 104 and all(row["candidate_status"] == "observed" and row["candidate_value"] == row["expected_health"] for row in translated)
        and not wrong and len(blank_rows) == 13 and all(row["status"] == "unknown" and row["value"] is None for row in blank_rows)
    ) else "FAIL_BOUNDED_ANCHOR_SEARCH"
    result = {
        "schema": "v39-hud-anchor-search-a01-v1", "execution_id": FREEZE["execution_id"], "status": status,
        "base_commit": base, "evidence_commit": evidence_commit, "freeze_sha256": sha((PACKAGE / "FREEZE.json").read_bytes()),
        "candidate_sha256": sha(Path(__file__).read_bytes()), "auditor_sha256": sha((PACKAGE / "audit.py").read_bytes()),
        "source_blobs": FREEZE["source_blobs"], "source_freeze_sha256": FREEZE["source_freeze_sha256"],
        "prior_freeze_sha256": FREEZE["prior_freeze_sha256"], "prior_result_sha256": FREEZE["prior_result_sha256"], "wad_sha256": sha(wad_bytes),
        "frame_count": len(baseline), "read_count": len(rows), "translated_count": len(translated), "perturbed_count": len(perturbed),
        "baseline_matches": sum(row["candidate_status"] == "observed" and row["candidate_value"] == row["expected_health"] for row in baseline),
        "translated_matches": sum(row["candidate_status"] == "observed" and row["candidate_value"] == row["expected_health"] for row in translated),
        "perturbed_unknown": sum(row["candidate_status"] == "unknown" for row in perturbed), "perturbed_observed_same": sum(row["candidate_status"] == "observed" and row["candidate_value"] == row["expected_health"] for row in perturbed),
        "perturbed_observed_wrong": len(wrong), "blank_controls": len(blank_rows), "blank_unknown": sum(row["status"] == "unknown" for row in blank_rows),
        "exact_reader_timing": exact_stats, "anchor_search_timing": candidate_stats,
        "p95_overhead_ratio": candidate_stats["p95_nearest_rank_ns"] / exact_stats["p95_nearest_rank_ns"],
        "rows": rows, "blank_rows": blank_rows,
        "runtime": {"python": sys.version.split()[0], "pillow": __import__("PIL").__version__, "numpy": np.__version__, "platform": sys.platform,
                    "game_or_gui_launched": False, "model_calls": 0, "os_input_emitted": False},
        "scope": FREEZE["scope"],
    }
    output = PACKAGE / "results" / "a01.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("execution_id", "status", "baseline_matches", "translated_matches", "perturbed_unknown", "perturbed_observed_wrong", "blank_unknown", "p95_overhead_ratio")}, sort_keys=True))
    return 0 if status == "PASS_BOUNDED_ANCHOR_SEARCH" else 1


if __name__ == "__main__":
    raise SystemExit(main())
