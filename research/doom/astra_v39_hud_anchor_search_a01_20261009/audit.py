"""Independent raw/source replay and mutation audit for anchor-search A01."""
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


def render_variants(source: Image.Image):
    yield "baseline", {}, source.copy()
    for dx, dy in FREEZE["translation_px"]:
        image = Image.new("RGB", source.size, (0, 0, 0))
        image.paste(source, (dx, dy))
        yield f"translate_{dx:+d}_{dy:+d}", {"dx": dx, "dy": dy}, image
    for factor in FREEZE["brightness_factors"]:
        yield f"brightness_{factor:.2f}", {"factor": factor}, ImageEnhance.Brightness(source).enhance(factor)
    for factor in FREEZE["contrast_factors"]:
        yield f"contrast_{factor:.2f}", {"factor": factor}, ImageEnhance.Contrast(source).enhance(factor)
    for quality in FREEZE["jpeg_qualities"]:
        compressed = io.BytesIO()
        source.save(compressed, format="JPEG", quality=quality, subsampling=0, optimize=False)
        data = compressed.getvalue()
        with Image.open(io.BytesIO(data)) as decoded:
            yield f"jpeg_q{quality}", {"quality": quality, "jpeg_sha256": sha(data)}, decoded.convert("RGB")


def independent_anchor_classification(reader, observation: dict, frame: Image.Image) -> dict:
    x0, y0, _, _ = observation["pointer_binding"]["geometry"]
    x0 += reader.local_anchor[0]
    y0 += reader.local_anchor[1]
    width, height = reader.glyph_size
    radius = FREEZE["anchor_search_radius_px"]
    matches = []
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            left, top = x0 + dx, y0 + dy
            if left < 0 or top < 0 or left + width * reader.slots > frame.width or top + height > frame.height:
                continue
            pixels = np.asarray(frame.convert("RGB").crop((left, top, left + width * reader.slots, top + height)))
            parsed = []
            score_rows = []
            ambiguous = False
            for slot in range(reader.slots):
                crop = pixels[:, slot * width:(slot + 1) * width]
                values = [int(np.count_nonzero(np.all(crop == template, axis=2)[mask])) / int(np.count_nonzero(mask))
                          for template, mask in reader.templates]
                order = sorted(range(10), key=values.__getitem__, reverse=True)
                best, second = order[0], order[1]
                if values[best] < reader.minimum_score or values[best] - values[second] < reader.minimum_margin:
                    ambiguous = True
                    break
                parsed.append(best)
                score_rows.append(values[best])
            if ambiguous:
                continue
            first = next((index for index, digit in enumerate(parsed) if digit is not None), None)
            if first is None or any(digit is None for digit in parsed[first:]) or any(digit is not None for digit in parsed[:first]):
                continue
            value = int("".join(str(digit) for digit in parsed[first:]))
            matches.append({"dx": dx, "dy": dy, "value": value, "mean_score": statistics.mean(score_rows)})
    values = sorted({row["value"] for row in matches})
    if not values:
        return {"status": "unknown", "value": None, "reason": "no_complete_anchor_match", "candidate_values": [], "chosen_offset": None, "matching_offset_count": 0}
    if len(values) > 1:
        return {"status": "unknown", "value": None, "reason": "conflicting_anchor_values", "candidate_values": values, "chosen_offset": None, "matching_offset_count": len(matches)}
    best = sorted(matches, key=lambda row: (-row["mean_score"], abs(row["dx"]) + abs(row["dy"]), abs(row["dy"]), abs(row["dx"])))[0]
    return {"status": "observed", "value": values[0], "reason": None, "candidate_values": values,
            "chosen_offset": {"dx": best["dx"], "dy": best["dy"]}, "matching_offset_count": len(matches)}


def blank_roi(image: Image.Image, binding: dict) -> Image.Image:
    output = image.convert("RGB").copy()
    left, top = binding["geometry"][0] + FREEZE["health_local_anchor"][0], binding["geometry"][1] + FREEZE["health_local_anchor"][1]
    width, height = FREEZE["glyph_size"]
    ImageDraw.Draw(output).rectangle((left, top, left + width * FREEZE["slots"] - 1, top + height - 1), fill=(0, 0, 0))
    return output


def metric_errors(result: dict, expected_rows: list[dict], expected_blanks: list[dict], exact_times: list[int], candidate_times: list[int]) -> list[str]:
    errors = []
    if type(result.get("rows")) is not list or len(result["rows"]) != len(expected_rows):
        return ["row count"]
    if type(result.get("blank_rows")) is not list or len(result["blank_rows"]) != len(expected_blanks):
        errors.append("blank row count")
        return errors
    for index, (actual, expected) in enumerate(zip(result["rows"], expected_rows, strict=True)):
        for key, value in expected.items():
            if actual.get(key) != value:
                errors.append(f"row {index} {key}")
    for index, (actual, expected) in enumerate(zip(result["blank_rows"], expected_blanks, strict=True)):
        for key, value in expected.items():
            if actual.get(key) != value:
                errors.append(f"blank row {index} {key}")
    baseline = [row for row in expected_rows if row["variant"] == "baseline"]
    translated = [row for row in expected_rows if row["variant"].startswith("translate_")]
    perturbed = [row for row in expected_rows if row["variant"] != "baseline"]
    wrong = sum(row["candidate_status"] == "observed" and row["candidate_value"] != row["expected_health"] for row in perturbed)
    expected_metrics = {
        "status": "PASS_BOUNDED_ANCHOR_SEARCH" if (len(baseline) == 13 and all(row["candidate_status"] == "observed" and row["candidate_value"] == row["expected_health"] for row in baseline)
                 and len(translated) == 104 and all(row["candidate_status"] == "observed" and row["candidate_value"] == row["expected_health"] for row in translated)
                 and wrong == 0 and len(expected_blanks) == 13 and all(row["status"] == "unknown" for row in expected_blanks)) else "FAIL_BOUNDED_ANCHOR_SEARCH",
        "frame_count": len(baseline), "read_count": len(expected_rows), "translated_count": len(translated), "perturbed_count": len(perturbed),
        "baseline_matches": sum(row["candidate_status"] == "observed" and row["candidate_value"] == row["expected_health"] for row in baseline),
        "translated_matches": sum(row["candidate_status"] == "observed" and row["candidate_value"] == row["expected_health"] for row in translated),
        "perturbed_unknown": sum(row["candidate_status"] == "unknown" for row in perturbed),
        "perturbed_observed_same": sum(row["candidate_status"] == "observed" and row["candidate_value"] == row["expected_health"] for row in perturbed),
        "perturbed_observed_wrong": wrong, "blank_controls": len(expected_blanks), "blank_unknown": sum(row["status"] == "unknown" for row in expected_blanks),
    }
    for key, value in expected_metrics.items():
        if result.get(key) != value:
            errors.append(f"metric {key}")
    exact_stats = {"n": len(exact_times), "median_ns": statistics.median(exact_times),
                   "p95_nearest_rank_ns": sorted(exact_times)[math.ceil(.95 * len(exact_times)) - 1], "max_ns": max(exact_times)}
    candidate_stats = {"n": len(candidate_times), "median_ns": statistics.median(candidate_times),
                       "p95_nearest_rank_ns": sorted(candidate_times)[math.ceil(.95 * len(candidate_times)) - 1], "max_ns": max(candidate_times)}
    if result.get("exact_reader_timing") != exact_stats:
        errors.append("exact timing summary")
    if result.get("anchor_search_timing") != candidate_stats:
        errors.append("candidate timing summary")
    if result.get("p95_overhead_ratio") != candidate_stats["p95_nearest_rank_ns"] / exact_stats["p95_nearest_rank_ns"]:
        errors.append("timing ratio")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wad", type=Path, required=True)
    parser.add_argument("--git-root", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    repo = args.git_root.resolve()
    result = json.loads((PACKAGE / "results" / "a01.json").read_text(encoding="utf-8"))
    errors = []
    base = FREEZE["base_commit"]
    evidence = FREEZE["evidence_commit"]
    if sha((PACKAGE / "FREEZE.json").read_bytes()) != result.get("freeze_sha256"):
        errors.append("freeze hash")
    if sha((PACKAGE / "analyze.py").read_bytes()) != FREEZE["candidate_sha256"] or result.get("candidate_sha256") != FREEZE["candidate_sha256"]:
        errors.append("candidate hash")
    if sha((PACKAGE / "audit.py").read_bytes()) != FREEZE["auditor_sha256"] or result.get("auditor_sha256") != FREEZE["auditor_sha256"]:
        errors.append("auditor hash")
    if result.get("base_commit") != base or result.get("evidence_commit") != evidence:
        errors.append("source commits")
    wad_sha = sha(args.wad.resolve().read_bytes())
    if wad_sha != FREEZE["wad_sha256"] or result.get("wad_sha256") != FREEZE["wad_sha256"]:
        errors.append("WAD hash")

    source_freeze_bytes = git_blob(repo, base, FREEZE["source_freeze_path"])
    prior_freeze_bytes = git_blob(repo, evidence, FREEZE["prior_freeze_path"])
    prior_result_bytes = git_blob(repo, evidence, FREEZE["prior_result_path"])
    if sha(source_freeze_bytes) != FREEZE["source_freeze_sha256"] or sha(prior_freeze_bytes) != FREEZE["prior_freeze_sha256"] or sha(prior_result_bytes) != FREEZE["prior_result_sha256"]:
        errors.append("pinned evidence hashes")
    source_freeze = json.loads(source_freeze_bytes)
    source_images = {}
    for frame in source_freeze["frames"]:
        frame_bytes = git_blob(repo, base, frame["frame_path"])
        if sha(frame_bytes) != frame["sha256"]:
            errors.append(f"frame hash {frame['frame_path']}")
        with Image.open(io.BytesIO(frame_bytes)) as opened:
            source_images[frame["index"]] = opened.convert("RGB")
    for path, expected_blob in FREEZE["source_blobs"].items():
        actual_blob = subprocess.check_output(["git", "rev-parse", f"{base}:{path}"], cwd=repo, text=True).strip()
        if actual_blob != expected_blob:
            errors.append(f"source blob {path}")

    with tempfile.TemporaryDirectory(prefix="v39-anchor-audit-") as temp:
        temp_root = Path(temp)
        for path in FREEZE["reader_modules"]:
            (temp_root / Path(path).name).write_bytes(git_blob(repo, base, path))
        sys.path.insert(0, str(temp_root))
        module = importlib.import_module("doom_hud_signal_v3")
        reader = module.DoomStatusNumberReader(args.wad, signal_id="health")
        expected_rows, expected_blanks, exact_times, candidate_times = [], [], [], []
        for frame in source_freeze["frames"]:
            source = source_images[frame["index"]]
            observation = {"sequence": frame["sequence"], "capture_ns": frame["capture_ns"], "pointer_binding": frame["pointer_binding"]}
            for variant, parameters, image in render_variants(source):
                exact = reader.read_frame(observation, image)
                independent = independent_anchor_classification(reader, observation, image)
                exact_times.append(1)
                candidate_times.append(1)
                expected_rows.append({
                    "frame_index": frame["index"], "source_path": frame["frame_path"], "source_png_sha256": frame["sha256"],
                    "sequence": frame["sequence"], "capture_ns": frame["capture_ns"], "pointer_binding": frame["pointer_binding"],
                    "expected_health": source_freeze["manual_health"][frame["index"]], "variant": variant, "parameters": parameters,
                    "transformed_rgb_sha256": rgb_digest(image), "exact_status": exact.get("status"), "exact_value": exact.get("value"),
                    "candidate_status": independent["status"], "candidate_value": independent["value"], "candidate_reason": independent["reason"],
                    "candidate_values": independent["candidate_values"], "chosen_offset": independent["chosen_offset"],
                    "matching_offset_count": independent["matching_offset_count"],
                })
            blank = blank_roi(source, frame["pointer_binding"])
            blank_independent = independent_anchor_classification(reader, observation, blank)
            expected_blanks.append({"frame_index": frame["index"], "sequence": frame["sequence"], "transformed_rgb_sha256": rgb_digest(blank),
                                    "status": blank_independent["status"], "value": blank_independent["value"], "reason": blank_independent["reason"]})

    # Validate candidate-reported timing fields separately; timings are raw one-pass measurements.
    actual_rows = result.get("rows", [])
    if len(actual_rows) == len(expected_rows):
        exact_times = [row.get("exact_elapsed_ns", 0) for row in actual_rows]
        candidate_times = [row.get("candidate_elapsed_ns", 0) for row in actual_rows]
        if any(type(value) is not int or value <= 0 for value in exact_times + candidate_times):
            errors.append("timing samples")
            exact_times = [max(1, value if type(value) is int else 1) for value in exact_times]
            candidate_times = [max(1, value if type(value) is int else 1) for value in candidate_times]
    else:
        exact_times = candidate_times = [1]
    errors.extend(metric_errors(result, expected_rows, expected_blanks, exact_times, candidate_times))

    controls = []
    for mutate in (
        lambda x: x["rows"][0].__setitem__("candidate_value", 999),
        lambda x: x["rows"].pop(),
        lambda x: x["rows"][0].__setitem__("transformed_rgb_sha256", "0" * 64),
        lambda x: x["blank_rows"][0].__setitem__("status", "observed"),
        lambda x: x.__setitem__("translated_matches", 0),
    ):
        mutant = copy.deepcopy(result)
        mutate(mutant)
        controls.append(bool(metric_errors(mutant, expected_rows, expected_blanks, exact_times, candidate_times)))
    if not all(controls):
        errors.append("mutation controls")

    audit = {
        "schema": "v39-hud-anchor-search-audit-a01-v1", "status": "PASS_AUDIT" if not errors else "FAIL_AUDIT",
        "errors": errors, "mutation_controls_passed": sum(controls), "mutation_controls_total": len(controls),
        "independently_recomputed_reads": len(expected_rows), "independently_recomputed_blank_controls": len(expected_blanks),
        "scope": "raw/source replay and result mutation audit; independent classification loop shares only the pinned WAD patch templates and Pillow/NumPy primitives",
    }
    (PACKAGE / "results" / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
