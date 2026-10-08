"""A03 probe: preserve exact-center reads, then search offsets only on pixel uncertainty."""
from __future__ import annotations

import argparse
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
FREEZE = json.loads((PACKAGE / "FREEZE_A03.json").read_text(encoding="utf-8"))


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


def classify_offset(reader, frame: Image.Image, observation: dict, dx: int, dy: int):
    x, y, _, _ = observation["pointer_binding"]["geometry"]
    left = x + reader.local_anchor[0] + dx
    top = y + reader.local_anchor[1] + dy
    width, height = reader.glyph_size
    if left < 0 or top < 0 or left + width * reader.slots > frame.width or top + height > frame.height:
        return None
    pixels = np.asarray(frame.convert("RGB").crop((left, top, left + width * reader.slots, top + height)))
    digits, scores_used = [], []
    for slot_index in range(reader.slots):
        crop = pixels[:, slot_index * width:(slot_index + 1) * width]
        scores = [float(np.all(crop == template, axis=2)[mask].mean()) for template, mask in reader.templates]
        order = sorted(range(10), key=scores.__getitem__, reverse=True)
        best, second = order[:2]
        if scores[best] < reader.minimum_score:
            digit = None
        elif scores[best] - scores[second] < reader.minimum_margin:
            return None
        else:
            digit = best
            scores_used.append(scores[best])
        digits.append(digit)
    first = next((index for index, digit in enumerate(digits) if digit is not None), None)
    if first is None or any(digit is None for digit in digits[first:]) or any(digit is not None for digit in digits[:first]):
        return None
    number = int("".join(str(digit) for digit in digits[first:]))
    return {"dx": dx, "dy": dy, "value": number, "mean_score": statistics.mean(scores_used)}


def anchor_fallback(reader, observation: dict, frame: Image.Image, exact: dict) -> dict:
    if exact.get("status") == "observed":
        return {"status": "observed", "value": exact["value"], "reason": None, "candidate_values": [exact["value"]],
                "source": "exact_center", "chosen_offset": {"dx": 0, "dy": 0}, "matching_offset_count": 1}
    if exact.get("reason") not in ("invalid_right_aligned_number", "ambiguous_digit"):
        return {"status": "unknown", "value": None, "reason": exact.get("reason", "center_unknown_not_searchable"),
                "candidate_values": [], "source": "fail_closed_before_search", "chosen_offset": None, "matching_offset_count": 0}
    radius = FREEZE["anchor_search_radius_px"]
    matches = []
    offsets = [(dx, 0) for dx in range(-radius, radius + 1) if dx] + [(0, dy) for dy in range(-radius, radius + 1) if dy]
    for dx, dy in offsets:
        match = classify_offset(reader, frame, observation, dx, dy)
        if match is not None:
            matches.append(match)
    values = sorted({match["value"] for match in matches})
    if not values:
        return {"status": "unknown", "value": None, "reason": "no_complete_anchor_match", "candidate_values": [],
                "source": "offset_search", "fallback_trigger_reason": exact.get("reason"), "chosen_offset": None, "matching_offset_count": 0}
    if len(values) > 1:
        return {"status": "unknown", "value": None, "reason": "conflicting_anchor_values", "candidate_values": values,
                "source": "offset_search", "fallback_trigger_reason": exact.get("reason"), "chosen_offset": None,
                "matching_offset_count": len(matches)}
    best = max(matches, key=lambda row: (row["mean_score"], -(abs(row["dx"]) + abs(row["dy"])), -abs(row["dy"]), -abs(row["dx"])))
    return {"status": "observed", "value": values[0], "reason": None, "candidate_values": values, "source": "offset_search",
            "fallback_trigger_reason": exact.get("reason"), "chosen_offset": {"dx": best["dx"], "dy": best["dy"]},
            "matching_offset_count": len(matches)}


def blank_roi(frame: Image.Image, binding: dict) -> Image.Image:
    output = frame.convert("RGB").copy()
    x, y = binding["geometry"][0] + FREEZE["health_local_anchor"][0], binding["geometry"][1] + FREEZE["health_local_anchor"][1]
    width, height = FREEZE["glyph_size"]
    ImageDraw.Draw(output).rectangle((x, y, x + width * FREEZE["slots"] - 1, y + height - 1), fill=(0, 0, 0))
    return output


def stats(values: list[int]) -> dict:
    ordered = sorted(values)
    return {"n": len(ordered), "median_ns": statistics.median(ordered),
            "p95_nearest_rank_ns": ordered[math.ceil(0.95 * len(ordered)) - 1], "max_ns": max(ordered)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wad", type=Path, required=True)
    parser.add_argument("--git-root", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    repo = args.git_root.resolve()
    if sha(Path(__file__).read_bytes()) != FREEZE["candidate_sha256"] or sha((PACKAGE / "audit_a03.py").read_bytes()) != FREEZE["auditor_sha256"]:
        raise SystemExit("HOLD_CODE_HASH")
    wad = args.wad.resolve().read_bytes()
    if sha(wad) != FREEZE["wad_sha256"]:
        raise SystemExit("HOLD_WAD_HASH")
    runtime = {"python": sys.version.split()[0], "pillow": __import__("PIL").__version__, "numpy": np.__version__}
    if runtime != FREEZE["runtime_versions"]:
        raise SystemExit("HOLD_RUNTIME_VERSION")
    base, evidence = FREEZE["base_commit"], FREEZE["evidence_commit"]
    source_bytes = git_blob(repo, base, FREEZE["source_freeze_path"])
    prior_a02 = (PACKAGE / FREEZE["prior_a02_result_path"]).read_bytes()
    prior_audit = (PACKAGE / FREEZE["prior_a02_audit_path"]).read_bytes()
    if sha(source_bytes) != FREEZE["source_freeze_sha256"] or sha(prior_a02) != FREEZE["prior_a02_result_sha256"] or sha(prior_audit) != FREEZE["prior_a02_audit_sha256"]:
        raise SystemExit("HOLD_PREDECESSOR_HASH")
    if json.loads(prior_a02)["status"] != FREEZE["prior_a02_expected_status"] or json.loads(prior_audit)["status"] != FREEZE["prior_a02_audit_expected_status"]:
        raise SystemExit("HOLD_PREDECESSOR_DISPOSITION")
    source_freeze = json.loads(source_bytes)
    for path, expected in FREEZE["source_blobs"].items():
        actual = subprocess.check_output(["git", "rev-parse", f"{base}:{path}"], cwd=repo, text=True).strip()
        if actual != expected:
            raise SystemExit(f"HOLD_SOURCE_BLOB:{path}")

    with tempfile.TemporaryDirectory(prefix="v39-anchor-a02-") as temp:
        module_root = Path(temp)
        for path in FREEZE["reader_modules"]:
            (module_root / Path(path).name).write_bytes(git_blob(repo, base, path))
        sys.path.insert(0, str(module_root))
        module = importlib.import_module("doom_hud_signal_v3")
        reader = module.DoomStatusNumberReader(args.wad, signal_id="health")
        rows, blanks = [], []
        for frame in source_freeze["frames"]:
            png = git_blob(repo, base, frame["frame_path"])
            if sha(png) != frame["sha256"]:
                raise SystemExit(f"HOLD_FRAME_HASH:{frame['frame_path']}")
            with Image.open(io.BytesIO(png)) as opened:
                original = opened.convert("RGB")
            observation = {"sequence": frame["sequence"], "capture_ns": frame["capture_ns"], "pointer_binding": frame["pointer_binding"]}
            for variant, parameters, image in variants(original):
                candidate_start = time.perf_counter_ns()
                exact = reader.read_frame(observation, image)
                exact_elapsed = time.perf_counter_ns() - candidate_start
                candidate = anchor_fallback(reader, observation, image, exact)
                full_elapsed = time.perf_counter_ns() - candidate_start
                rows.append({
                    "frame_index": frame["index"], "source_path": frame["frame_path"], "source_png_sha256": frame["sha256"],
                    "sequence": frame["sequence"], "capture_ns": frame["capture_ns"], "pointer_binding": frame["pointer_binding"],
                    "expected_health": source_freeze["manual_health"][frame["index"]], "variant": variant, "parameters": parameters,
                    "transformed_rgb_sha256": rgb_digest(image), "exact_status": exact.get("status"), "exact_value": exact.get("value"),
                    "exact_reason": exact.get("reason"), "exact_elapsed_ns": exact_elapsed, "candidate_status": candidate["status"],
                    "candidate_value": candidate["value"], "candidate_reason": candidate["reason"], "candidate_values": candidate["candidate_values"],
                    "candidate_source": candidate["source"], "fallback_trigger_reason": candidate.get("fallback_trigger_reason"),
                    "chosen_offset": candidate["chosen_offset"], "matching_offset_count": candidate["matching_offset_count"],
                    "candidate_elapsed_ns": full_elapsed,
                })
            blank = blank_roi(original, frame["pointer_binding"])
            exact_blank = reader.read_frame(observation, blank)
            candidate_blank = anchor_fallback(reader, observation, blank, exact_blank)
            blanks.append({"frame_index": frame["index"], "sequence": frame["sequence"], "transformed_rgb_sha256": rgb_digest(blank),
                           "exact_status": exact_blank["status"], "status": candidate_blank["status"], "value": candidate_blank["value"],
                           "reason": candidate_blank["reason"], "source": candidate_blank["source"]})

    baseline = [row for row in rows if row["variant"] == "baseline"]
    translated = [row for row in rows if row["variant"].startswith("translate_")]
    perturbed = [row for row in rows if row["variant"] != "baseline"]
    wrong = sum(row["candidate_status"] == "observed" and row["candidate_value"] != row["expected_health"] for row in perturbed)
    base_stats = stats([row["exact_elapsed_ns"] for row in rows])
    candidate_stats = stats([row["candidate_elapsed_ns"] for row in rows])
    status = "PASS_BOUNDED_CROSS_SEARCH" if (
        len(baseline) == 13 and all(row["candidate_status"] == "observed" and row["candidate_value"] == row["expected_health"] for row in baseline)
        and len(translated) == 104 and all(row["candidate_status"] == "observed" and row["candidate_value"] == row["expected_health"] for row in translated)
        and wrong == 0 and len(blanks) == 13 and all(row["status"] == "unknown" and row["value"] is None for row in blanks)
    ) else "FAIL_BOUNDED_CROSS_SEARCH"
    result = {
        "schema": "v39-hud-anchor-search-a03-v1", "execution_id": FREEZE["execution_id"], "status": status,
        "base_commit": base, "evidence_commit": evidence, "freeze_sha256": sha((PACKAGE / "FREEZE_A03.json").read_bytes()),
        "candidate_sha256": sha(Path(__file__).read_bytes()), "auditor_sha256": sha((PACKAGE / "audit_a03.py").read_bytes()),
        "source_blobs": FREEZE["source_blobs"], "source_freeze_sha256": FREEZE["source_freeze_sha256"],
        "prior_a02_result_sha256": FREEZE["prior_a02_result_sha256"], "prior_a02_audit_sha256": FREEZE["prior_a02_audit_sha256"],
        "wad_sha256": sha(wad), "frame_count": len(baseline), "read_count": len(rows), "translated_count": len(translated),
        "perturbed_count": len(perturbed), "baseline_matches": sum(row["candidate_status"] == "observed" and row["candidate_value"] == row["expected_health"] for row in baseline),
        "translated_matches": sum(row["candidate_status"] == "observed" and row["candidate_value"] == row["expected_health"] for row in translated),
        "perturbed_unknown": sum(row["candidate_status"] == "unknown" for row in perturbed),
        "perturbed_observed_same": sum(row["candidate_status"] == "observed" and row["candidate_value"] == row["expected_health"] for row in perturbed),
        "perturbed_observed_wrong": wrong, "blank_controls": len(blanks), "blank_unknown": sum(row["status"] == "unknown" for row in blanks),
        "exact_reader_timing": base_stats, "candidate_end_to_end_timing": candidate_stats,
        "p95_overhead_ratio": candidate_stats["p95_nearest_rank_ns"] / base_stats["p95_nearest_rank_ns"],
        "rows": rows, "blank_rows": blanks, "runtime": {**runtime, "platform": sys.platform, "game_or_gui_launched": False, "model_calls": 0, "os_input_emitted": False},
        "scope": FREEZE["scope"],
    }
    (PACKAGE / "results" / "a03.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("execution_id", "status", "baseline_matches", "translated_matches", "perturbed_unknown", "perturbed_observed_wrong", "blank_unknown", "p95_overhead_ratio")}, sort_keys=True))
    return 0 if status == "PASS_BOUNDED_CROSS_SEARCH" else 1


if __name__ == "__main__":
    raise SystemExit(main())
