"""A04: compare the retained 8-axis fallback with a 24-position square scan."""
import argparse
import hashlib
import importlib
import io
import json
import subprocess
import sys
import tempfile
import math
import statistics
import time
from pathlib import Path

from PIL import Image, ImageDraw
import numpy as np


HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "FREEZE_A04.json").read_text(encoding="utf-8"))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def blob(repo, commit, path):
    return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=repo)


def rgb_digest(image):
    image = image.convert("RGB")
    width, height = image.size
    return digest(width.to_bytes(4, "big") + height.to_bytes(4, "big") + image.tobytes())


def shifted(image, dx, dy):
    result = Image.new("RGB", image.size, (0, 0, 0))
    result.paste(image, (dx, dy))
    return result


def classify_offset(reader, frame, observation, dx, dy):
    x, y, _, _ = observation["pointer_binding"]["geometry"]
    left = x + reader.local_anchor[0] + dx
    top = y + reader.local_anchor[1] + dy
    width, height = reader.glyph_size
    if (left < 0 or top < 0 or left + width * reader.slots > frame.width
            or top + height > frame.height):
        return None
    pixels = np.asarray(frame.convert("RGB").crop(
        (left, top, left + width * reader.slots, top + height)))
    digits, confidences = [], []
    for slot in range(reader.slots):
        crop = pixels[:, slot * width:(slot + 1) * width]
        scores = [float(np.all(crop == template, axis=2)[mask].mean())
                  for template, mask in reader.templates]
        best, second = sorted(range(10), key=scores.__getitem__, reverse=True)[:2]
        if scores[best] < reader.minimum_score:
            digit = None
        elif scores[best] - scores[second] < reader.minimum_margin:
            return None
        else:
            digit = best
            confidences.append(scores[best])
        digits.append(digit)
    first = next((index for index, digit in enumerate(digits) if digit is not None), None)
    if (first is None or any(digit is None for digit in digits[first:])
            or any(digit is not None for digit in digits[:first])):
        return None
    return {
        "dx": dx,
        "dy": dy,
        "value": int("".join(str(digit) for digit in digits[first:])),
        "mean_score": sum(confidences) / len(confidences),
    }


def fallback(reader, observation, frame, exact, offsets):
    if exact.get("status") == "observed":
        return {"status": "observed", "value": exact["value"], "reason": None,
                "candidate_values": [exact["value"]], "source": "exact_center",
                "chosen_offset": {"dx": 0, "dy": 0}, "matching_offset_count": 1}
    if exact.get("reason") not in ("invalid_right_aligned_number", "ambiguous_digit"):
        return {"status": "unknown", "value": None,
                "reason": exact.get("reason", "center_unknown_not_searchable"),
                "candidate_values": [], "source": "fail_closed_before_search",
                "chosen_offset": None, "matching_offset_count": 0}
    matches = []
    for dx, dy in offsets:
        match = classify_offset(reader, frame, observation, dx, dy)
        if match is not None:
            matches.append(match)
    values = sorted({item["value"] for item in matches})
    if not values:
        return {"status": "unknown", "value": None,
                "reason": "no_complete_anchor_match", "candidate_values": [],
                "source": "offset_search", "chosen_offset": None,
                "matching_offset_count": 0}
    if len(values) > 1:
        return {"status": "unknown", "value": None,
                "reason": "conflicting_anchor_values", "candidate_values": values,
                "source": "offset_search", "chosen_offset": None,
                "matching_offset_count": len(matches)}
    best = max(matches, key=lambda item: (
        item["mean_score"], -(abs(item["dx"]) + abs(item["dy"])),
        -abs(item["dy"]), -abs(item["dx"])))
    return {"status": "observed", "value": values[0], "reason": None,
            "candidate_values": values, "source": "offset_search",
            "chosen_offset": {"dx": best["dx"], "dy": best["dy"]},
            "matching_offset_count": len(matches)}


def blank_roi(frame, binding):
    output = frame.convert("RGB").copy()
    left = binding["geometry"][0] + FREEZE["health_local_anchor"][0]
    top = binding["geometry"][1] + FREEZE["health_local_anchor"][1]
    width, height = FREEZE["glyph_size"]
    ImageDraw.Draw(output).rectangle(
        (left, top, left + width * FREEZE["slots"] - 1, top + height - 1),
        fill=(0, 0, 0))
    return output


def summarize(rows, blanks):
    baseline = [row for row in rows if row["variant"] == "baseline"]
    diagonal = [row for row in rows if row["variant"] == "diagonal"]
    summary = {"frame_count": len(baseline), "diagonal_count": len(diagonal)}
    for arm in ("axis", "square"):
        summary[arm] = {
            "baseline_correct": sum(
                row[arm]["status"] == "observed" and
                row[arm]["value"] == row["expected_health"] for row in baseline),
            "diagonal_correct": sum(
                row[arm]["status"] == "observed" and
                row[arm]["value"] == row["expected_health"] for row in diagonal),
            "diagonal_wrong_observed": sum(
                row[arm]["status"] == "observed" and
                row[arm]["value"] != row["expected_health"] for row in diagonal),
            "diagonal_unknown": sum(row[arm]["status"] == "unknown" for row in diagonal),
        }
    summary["blank_controls"] = len(blanks)
    summary["axis_blank_unknown"] = sum(row["axis"]["status"] == "unknown" for row in blanks)
    summary["square_blank_unknown"] = sum(row["square"]["status"] == "unknown" for row in blanks)
    for arm in ("axis", "square"):
        samples = sorted(row[arm]["elapsed_ns"] for row in rows)
        summary[arm]["timing_ns"] = {
            "n": len(samples),
            "median": statistics.median(samples),
            "p95_nearest_rank": samples[math.ceil(0.95 * len(samples)) - 1],
            "max": max(samples),
        }
    passed = (
        len(baseline) == FREEZE["frame_count"]
        and summary["axis"]["baseline_correct"] == FREEZE["frame_count"]
        and summary["square"]["baseline_correct"] == FREEZE["frame_count"]
        and len(diagonal) == FREEZE["frame_count"] * len(FREEZE["diagonal_translations"])
        and summary["square"]["diagonal_correct"] == len(diagonal)
        and summary["square"]["diagonal_wrong_observed"] == 0
        and summary["square_blank_unknown"] == FREEZE["frame_count"]
    )
    summary["disposition"] = "PASS_SQUARE_DIAGONAL_RECOVERY" if passed else "FAIL_SQUARE_DIAGONAL_RECOVERY"
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wad", type=Path, required=True)
    parser.add_argument("--git-root", type=Path, default=HERE.parents[3])
    args = parser.parse_args()
    repo = args.git_root.resolve()
    base = FREEZE["base_commit"]
    if (digest(Path(__file__).read_bytes()) != FREEZE["candidate_sha256"]
            or digest((HERE / "audit_a04.py").read_bytes()) != FREEZE["auditor_sha256"]):
        raise SystemExit("HOLD_CODE_HASH")
    wad = args.wad.resolve().read_bytes()
    if digest(wad) != FREEZE["wad_sha256"]:
        raise SystemExit("HOLD_WAD_HASH")
    runtime = {"python": sys.version.split()[0], "numpy": np.__version__,
               "pillow": __import__("PIL").__version__}
    if runtime != FREEZE["runtime_versions"]:
        raise SystemExit("HOLD_RUNTIME")
    source_freeze_bytes = blob(repo, base, FREEZE["source_freeze_path"])
    if digest(source_freeze_bytes) != FREEZE["source_freeze_sha256"]:
        raise SystemExit("HOLD_SOURCE_FREEZE")
    source_freeze = json.loads(source_freeze_bytes)
    for path, expected in FREEZE["reader_blobs"].items():
        actual = subprocess.check_output(["git", "rev-parse", f"{base}:{path}"],
                                          cwd=repo, text=True).strip()
        if actual != expected:
            raise SystemExit(f"HOLD_READER_BLOB:{path}")
    prior_result_bytes = blob(repo, base, FREEZE["prior_a03_result_path"])
    prior_audit_bytes = blob(repo, base, FREEZE["prior_a03_audit_path"])
    if (digest(prior_result_bytes) != FREEZE["prior_a03_result_sha256"]
            or digest(prior_audit_bytes) != FREEZE["prior_a03_audit_sha256"]):
        raise SystemExit("HOLD_A03_PREDECESSOR_HASH")
    prior_result = json.loads(prior_result_bytes)
    prior_audit = json.loads(prior_audit_bytes)
    if (prior_result.get("status") != "PASS_BOUNDED_CROSS_SEARCH"
            or prior_audit.get("errors") != []
            or prior_audit.get("mutation_controls_passed") != 5):
        raise SystemExit("HOLD_A03_PREDECESSOR")

    with tempfile.TemporaryDirectory(prefix="hud-diagonal-a04-reader-") as temp:
        module_root = Path(temp)
        for path in FREEZE["reader_blobs"]:
            (module_root / Path(path).name).write_bytes(blob(repo, base, path))
        sys.path.insert(0, str(module_root))
        reader_module = importlib.import_module("doom_hud_signal_v3")
        reader = reader_module.DoomStatusNumberReader(
            args.wad, signal_id="health", expected_wad_sha256=FREEZE["wad_sha256"])
        rows, blanks = [], []
        axis = [tuple(pair) for pair in FREEZE["axis_offsets"]]
        square = [tuple(pair) for pair in FREEZE["square_offsets"]]
        for frame_meta in source_freeze["frames"]:
            raw = blob(repo, base, frame_meta["frame_path"])
            if digest(raw) != frame_meta["sha256"]:
                raise SystemExit(f"HOLD_FRAME_HASH:{frame_meta['frame_path']}")
            with Image.open(io.BytesIO(raw)) as opened:
                original = opened.convert("RGB")
            observation = {"sequence": frame_meta["sequence"],
                           "capture_ns": frame_meta["capture_ns"],
                           "pointer_binding": frame_meta["pointer_binding"]}
            truth = source_freeze["manual_health"][frame_meta["index"]]
            cases = [("baseline", 0, 0, original)]
            for dx, dy in FREEZE["diagonal_translations"]:
                cases.append(("diagonal", dx, dy, shifted(original, dx, dy)))
            for case_index, (variant, dx, dy, image) in enumerate(cases):
                exact = reader.read_frame(observation, image)
                order = ["axis", "square"] if case_index % 2 == 0 else ["square", "axis"]
                measured = {}
                for arm in order:
                    offsets = axis if arm == "axis" else square
                    start = time.perf_counter_ns()
                    measured[arm] = fallback(reader, observation, image, exact, offsets)
                    measured[arm]["elapsed_ns"] = time.perf_counter_ns() - start
                rows.append({
                    "frame_index": frame_meta["index"],
                    "frame_path": frame_meta["frame_path"],
                    "source_png_sha256": frame_meta["sha256"],
                    "expected_health": truth,
                    "variant": variant,
                    "translation": {"dx": dx, "dy": dy},
                    "transformed_rgb_sha256": rgb_digest(image),
                    "exact": {"status": exact.get("status"), "value": exact.get("value"),
                              "reason": exact.get("reason")},
                    "arm_order": order,
                    "axis": measured["axis"],
                    "square": measured["square"],
                })
            blank = blank_roi(original, frame_meta["pointer_binding"])
            exact_blank = reader.read_frame(observation, blank)
            blank_order = ["axis", "square"] if frame_meta["index"] % 2 == 0 else ["square", "axis"]
            blank_measured = {}
            for arm in blank_order:
                offsets = axis if arm == "axis" else square
                start = time.perf_counter_ns()
                blank_measured[arm] = fallback(reader, observation, blank, exact_blank, offsets)
                blank_measured[arm]["elapsed_ns"] = time.perf_counter_ns() - start
            blanks.append({
                "frame_index": frame_meta["index"],
                "transformed_rgb_sha256": rgb_digest(blank),
                "exact": {"status": exact_blank.get("status"),
                          "value": exact_blank.get("value"),
                          "reason": exact_blank.get("reason")},
                "arm_order": blank_order,
                "axis": blank_measured["axis"],
                "square": blank_measured["square"],
            })

    summary = summarize(rows, blanks)
    result = {
        "schema": "v39-hud-anchor-diagonal-a04-v1",
        "execution_id": FREEZE["execution_id"],
        "base_commit": base,
        "source_freeze_sha256": FREEZE["source_freeze_sha256"],
        "reader_blobs": FREEZE["reader_blobs"],
        "wad_sha256": digest(wad),
        "candidate_sha256": digest(Path(__file__).read_bytes()),
        "auditor_sha256": FREEZE["auditor_sha256"],
        "freeze_sha256": digest((HERE / "FREEZE_A04.json").read_bytes()),
        "runtime": {**runtime, "platform": sys.platform,
                    "gui_or_game_launched": False, "model_calls": 0,
                    "os_input_emitted": False},
        "offsets": {"axis": axis, "square": square,
                    "tested_diagonals": FREEZE["diagonal_translations"]},
        "rows": rows,
        "blank_rows": blanks,
        "summary": summary,
    }
    output = HERE / "results" / "a04.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"execution_id": FREEZE["execution_id"],
                      "summary": summary, "result_path": str(output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
