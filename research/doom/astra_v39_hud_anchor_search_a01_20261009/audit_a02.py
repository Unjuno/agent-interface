"""Independent source replay and mutation controls for bounded HUD search A02."""
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
FREEZE = json.loads((PACKAGE / "FREEZE_A02.json").read_text(encoding="utf-8"))


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
        image = Image.new("RGB", source.size, (0, 0, 0))
        image.paste(source, (dx, dy))
        yield f"translate_{dx:+d}_{dy:+d}", {"dx": dx, "dy": dy}, image
    for factor in FREEZE["brightness_factors"]:
        yield f"brightness_{factor:.2f}", {"factor": factor}, ImageEnhance.Brightness(source).enhance(factor)
    for factor in FREEZE["contrast_factors"]:
        yield f"contrast_{factor:.2f}", {"factor": factor}, ImageEnhance.Contrast(source).enhance(factor)
    for quality in FREEZE["jpeg_qualities"]:
        encoded = io.BytesIO()
        source.save(encoded, format="JPEG", quality=quality, subsampling=0, optimize=False)
        data = encoded.getvalue()
        with Image.open(io.BytesIO(data)) as reopened:
            yield f"jpeg_q{quality}", {"quality": quality, "jpeg_sha256": sha(data)}, reopened.convert("RGB")


def independently_classify(reader, observation: dict, frame: Image.Image, radius: int):
    x, y, _, _ = observation["pointer_binding"]["geometry"]
    x += reader.local_anchor[0]
    y += reader.local_anchor[1]
    width, height = reader.glyph_size
    matches = []
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            left, top = x + dx, y + dy
            if left < 0 or top < 0 or left + width * reader.slots > frame.width or top + height > frame.height:
                continue
            pixels = np.asarray(frame.convert("RGB").crop((left, top, left + width * reader.slots, top + height)))
            parsed = []
            score_sum = 0.0
            valid = True
            for slot in range(reader.slots):
                crop = pixels[:, slot * width:(slot + 1) * width]
                scores = [int(np.count_nonzero(np.all(crop == template, axis=2)[mask])) / int(np.count_nonzero(mask))
                          for template, mask in reader.templates]
                best, second = sorted(range(10), key=scores.__getitem__, reverse=True)[:2]
                if scores[best] < reader.minimum_score:
                    parsed.append(None)
                elif scores[best] - scores[second] < reader.minimum_margin:
                    valid = False
                    break
                else:
                    parsed.append(best)
                    score_sum += scores[best]
            if not valid:
                continue
            first = next((i for i, digit in enumerate(parsed) if digit is not None), None)
            if first is None or any(d is None for d in parsed[first:]) or any(d is not None for d in parsed[:first]):
                continue
            matches.append({"dx": dx, "dy": dy, "value": int("".join(str(d) for d in parsed[first:])),
                            "mean_score": score_sum / (reader.slots - first)})
    values = sorted({item["value"] for item in matches})
    if not values:
        return {"status": "unknown", "value": None, "reason": "no_complete_anchor_match", "candidate_values": [],
                "source": "offset_search", "fallback_trigger_reason": None, "chosen_offset": None, "matching_offset_count": 0}
    if len(values) > 1:
        return {"status": "unknown", "value": None, "reason": "conflicting_anchor_values", "candidate_values": values,
                "source": "offset_search", "fallback_trigger_reason": None, "chosen_offset": None, "matching_offset_count": len(matches)}
    best = sorted(matches, key=lambda item: (-item["mean_score"], abs(item["dx"]) + abs(item["dy"]), abs(item["dy"]), abs(item["dx"])))[0]
    return {"status": "observed", "value": values[0], "reason": None, "candidate_values": values, "source": "offset_search",
            "fallback_trigger_reason": None, "chosen_offset": {"dx": best["dx"], "dy": best["dy"]}, "matching_offset_count": len(matches)}


def independent_decision(reader, observation: dict, frame: Image.Image):
    exact = reader.read_frame(observation, frame)
    if exact.get("status") == "observed":
        decision = {"status": "observed", "value": exact["value"], "reason": None, "candidate_values": [exact["value"]],
                    "source": "exact_center", "fallback_trigger_reason": None, "chosen_offset": {"dx": 0, "dy": 0}, "matching_offset_count": 1}
        return exact, decision
    if exact.get("reason") not in ("invalid_right_aligned_number", "ambiguous_digit"):
        return exact, {"status": "unknown", "value": None, "reason": exact.get("reason", "center_unknown_not_searchable"),
                       "candidate_values": [], "source": "fail_closed_before_search", "fallback_trigger_reason": None,
                       "chosen_offset": None, "matching_offset_count": 0}
    decision = independently_classify(reader, observation, frame, FREEZE["anchor_search_radius_px"])
    decision["fallback_trigger_reason"] = exact.get("reason")
    return exact, decision


def blank_roi(frame: Image.Image, binding: dict):
    result = frame.convert("RGB").copy()
    left = binding["geometry"][0] + FREEZE["health_local_anchor"][0]
    top = binding["geometry"][1] + FREEZE["health_local_anchor"][1]
    width, height = FREEZE["glyph_size"]
    ImageDraw.Draw(result).rectangle((left, top, left + width * FREEZE["slots"] - 1, top + height - 1), fill=(0, 0, 0))
    return result


def timing(values):
    ordered = sorted(values)
    return {"n": len(ordered), "median_ns": statistics.median(ordered),
            "p95_nearest_rank_ns": ordered[math.ceil(.95 * len(ordered)) - 1], "max_ns": max(ordered)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wad", type=Path, required=True)
    parser.add_argument("--git-root", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    repo = args.git_root.resolve()
    result = json.loads((PACKAGE / "results" / "a02.json").read_text(encoding="utf-8"))
    errors = []
    def check(condition, label):
        if not condition:
            errors.append(label)
    check(sha((PACKAGE / "FREEZE_A02.json").read_bytes()) == result.get("freeze_sha256"), "freeze hash")
    check(sha((PACKAGE / "analyze_a02.py").read_bytes()) == FREEZE["candidate_sha256"] == result.get("candidate_sha256"), "candidate hash")
    check(sha(Path(__file__).read_bytes()) == FREEZE["auditor_sha256"] == result.get("auditor_sha256"), "auditor hash")
    check(result.get("base_commit") == FREEZE["base_commit"] and result.get("evidence_commit") == FREEZE["evidence_commit"], "source commits")
    check(sha(args.wad.resolve().read_bytes()) == FREEZE["wad_sha256"] == result.get("wad_sha256"), "WAD hash")
    source_freeze_bytes = git_blob(repo, FREEZE["base_commit"], FREEZE["source_freeze_path"])
    prior_result = (PACKAGE / FREEZE["prior_a01_result_path"]).read_bytes()
    prior_audit = (PACKAGE / FREEZE["prior_a01_audit_path"]).read_bytes()
    check(sha(source_freeze_bytes) == FREEZE["source_freeze_sha256"], "source freeze hash")
    check(sha(prior_result) == FREEZE["prior_a01_result_sha256"], "prior A01 result hash")
    check(sha(prior_audit) == FREEZE["prior_a01_audit_sha256"], "prior A01 audit hash")
    prior = json.loads(prior_result)
    prior_audit_data = json.loads(prior_audit)
    check(prior.get("status") == FREEZE["prior_a01_expected_status"], "prior A01 status")
    check(prior_audit_data.get("status") == FREEZE["prior_a01_audit_expected_status"], "prior A01 audit status")
    source_freeze = json.loads(source_freeze_bytes)
    for path, blob in FREEZE["source_blobs"].items():
        actual = subprocess.check_output(["git", "rev-parse", f"{FREEZE['base_commit']}:{path}"], cwd=repo, text=True).strip()
        check(actual == blob, f"source blob {path}")
    with tempfile.TemporaryDirectory(prefix="v39-anchor-a02-audit-") as temp:
        root = Path(temp)
        for path in FREEZE["reader_modules"]:
            (root / Path(path).name).write_bytes(git_blob(repo, FREEZE["base_commit"], path))
        sys.path.insert(0, str(root))
        module = importlib.import_module("doom_hud_signal_v3")
        reader = module.DoomStatusNumberReader(args.wad, signal_id="health")
        expected_rows, expected_blanks, images_by_frame = [], [], {}
        for frame in source_freeze["frames"]:
            raw = git_blob(repo, FREEZE["base_commit"], frame["frame_path"])
            check(sha(raw) == frame["sha256"], f"frame hash {frame['frame_path']}")
            with Image.open(io.BytesIO(raw)) as opened:
                original = opened.convert("RGB")
            images_by_frame[frame["index"]] = original
            observation = {"sequence": frame["sequence"], "capture_ns": frame["capture_ns"], "pointer_binding": frame["pointer_binding"]}
            for name, parameters, image in variants(original):
                exact, decision = independent_decision(reader, observation, image)
                expected_rows.append({
                    "frame_index": frame["index"], "source_path": frame["frame_path"], "source_png_sha256": frame["sha256"],
                    "sequence": frame["sequence"], "capture_ns": frame["capture_ns"], "pointer_binding": frame["pointer_binding"],
                    "expected_health": source_freeze["manual_health"][frame["index"]], "variant": name, "parameters": parameters,
                    "transformed_rgb_sha256": rgb_digest(image), "exact_status": exact.get("status"), "exact_value": exact.get("value"),
                    "exact_reason": exact.get("reason"), "candidate_status": decision["status"], "candidate_value": decision["value"],
                    "candidate_reason": decision["reason"], "candidate_values": decision["candidate_values"], "candidate_source": decision["source"],
                    "fallback_trigger_reason": decision["fallback_trigger_reason"], "chosen_offset": decision["chosen_offset"],
                    "matching_offset_count": decision["matching_offset_count"],
                })
            blank = blank_roi(original, frame["pointer_binding"])
            exact_blank, decision_blank = independent_decision(reader, observation, blank)
            expected_blanks.append({"frame_index": frame["index"], "sequence": frame["sequence"], "transformed_rgb_sha256": rgb_digest(blank),
                                    "exact_status": exact_blank.get("status"), "status": decision_blank["status"], "value": decision_blank["value"],
                                    "reason": decision_blank["reason"], "source": decision_blank["source"]})

    actual_rows = result.get("rows") if isinstance(result.get("rows"), list) else []
    actual_blanks = result.get("blank_rows") if isinstance(result.get("blank_rows"), list) else []
    check(len(actual_rows) == len(expected_rows), "row count")
    check(len(actual_blanks) == len(expected_blanks), "blank row count")
    for i, (actual, expected) in enumerate(zip(actual_rows, expected_rows)):
        for key, value in expected.items():
            check(actual.get(key) == value, f"row {i} {key}")
    for i, (actual, expected) in enumerate(zip(actual_blanks, expected_blanks)):
        for key, value in expected.items():
            check(actual.get(key) == value, f"blank row {i} {key}")
    baseline = [r for r in expected_rows if r["variant"] == "baseline"]
    translated = [r for r in expected_rows if r["variant"].startswith("translate_")]
    perturbed = [r for r in expected_rows if r["variant"] != "baseline"]
    wrong = sum(r["candidate_status"] == "observed" and r["candidate_value"] != r["expected_health"] for r in perturbed)
    want_status = "PASS_BOUNDED_ANCHOR_SEARCH" if len(baseline) == 13 and all(r["candidate_status"] == "observed" and r["candidate_value"] == r["expected_health"] for r in baseline) and len(translated) == 104 and all(r["candidate_status"] == "observed" and r["candidate_value"] == r["expected_health"] for r in translated) and wrong == 0 and len(expected_blanks) == 13 and all(r["status"] == "unknown" and r["value"] is None for r in expected_blanks) else "FAIL_BOUNDED_ANCHOR_SEARCH"
    exact_times = [r.get("exact_elapsed_ns") for r in actual_rows]
    candidate_times = [r.get("candidate_elapsed_ns") for r in actual_rows]
    check(all(type(v) is int and v > 0 for v in exact_times + candidate_times), "positive timing samples")
    if exact_times and candidate_times and all(type(v) is int and v > 0 for v in exact_times + candidate_times):
        exact_stats, candidate_stats = timing(exact_times), timing(candidate_times)
        check(result.get("exact_reader_timing") == exact_stats, "exact timing summary")
        check(result.get("candidate_end_to_end_timing") == candidate_stats, "candidate timing summary")
        check(result.get("p95_overhead_ratio") == candidate_stats["p95_nearest_rank_ns"] / exact_stats["p95_nearest_rank_ns"], "timing ratio")
    metrics = {
        "status": want_status, "frame_count": len(baseline), "read_count": len(expected_rows), "translated_count": len(translated),
        "perturbed_count": len(perturbed), "baseline_matches": sum(r["candidate_status"] == "observed" and r["candidate_value"] == r["expected_health"] for r in baseline),
        "translated_matches": sum(r["candidate_status"] == "observed" and r["candidate_value"] == r["expected_health"] for r in translated),
        "perturbed_unknown": sum(r["candidate_status"] == "unknown" for r in perturbed),
        "perturbed_observed_same": sum(r["candidate_status"] == "observed" and r["candidate_value"] == r["expected_health"] for r in perturbed),
        "perturbed_observed_wrong": wrong, "blank_controls": len(expected_blanks), "blank_unknown": sum(r["status"] == "unknown" for r in expected_blanks),
    }
    for key, value in metrics.items():
        check(result.get(key) == value, f"metric {key}")

    # Independent mutation checks: each targeted field must make the audit fail.
    controls = []
    def detects(mutator):
        mutated = copy.deepcopy(result)
        mutator(mutated)
        bad = any(mutated.get(k) != v for k, v in metrics.items())
        if not bad and mutated.get("rows"):
            bad = mutated["rows"][0].get("candidate_value") != expected_rows[0]["candidate_value"]
        if not bad and mutated.get("blank_rows"):
            bad = mutated["blank_rows"][0].get("status") != expected_blanks[0]["status"]
        return bad
    controls.append(detects(lambda x: x["rows"][0].__setitem__("candidate_value", 999)))
    controls.append(detects(lambda x: x["rows"][0].__setitem__("transformed_rgb_sha256", "0" * 64)))
    controls.append(detects(lambda x: x["blank_rows"][0].__setitem__("status", "observed")))
    controls.append(detects(lambda x: x.__setitem__("translated_matches", 0)))
    controls.append(detects(lambda x: x.__setitem__("p95_overhead_ratio", 0)))
    check(all(controls), "mutation controls")
    audit = {"schema": "v39-hud-anchor-search-a02-audit-v1", "status": "PASS_AUDIT" if not errors else "FAIL_AUDIT",
             "errors": errors, "mutation_controls_passed": sum(controls), "mutation_controls_total": len(controls),
             "reconstructed": metrics, "scope": "independent image replay, provenance, metrics, and copied-result mutation audit; offline evidence only"}
    (PACKAGE / "results" / "audit_a02.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": audit["status"], "errors": errors[:12], "mutation_controls_passed": audit["mutation_controls_passed"]}, sort_keys=True))
    return 0 if audit["status"] == "PASS_AUDIT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
