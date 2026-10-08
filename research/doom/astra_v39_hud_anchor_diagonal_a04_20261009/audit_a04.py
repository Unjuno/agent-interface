"""Independent pixel-path audit of the frozen A04 candidate output."""
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
from PIL import Image, ImageDraw


HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "FREEZE_A04.json").read_text(encoding="utf-8"))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def blob(repo, commit, path):
    return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=repo)


def rgb_digest(image):
    image = image.convert("RGB")
    return digest(image.width.to_bytes(4, "big") + image.height.to_bytes(4, "big")
                  + image.tobytes())


def shifted(source, dx, dy):
    target = Image.new("RGB", source.size, (0, 0, 0))
    target.paste(source, (dx, dy))
    return target


def independent_classify(reader, image, observation, dx, dy):
    origin_x, origin_y, _, _ = observation["pointer_binding"]["geometry"]
    x = origin_x + reader.local_anchor[0] + dx
    y = origin_y + reader.local_anchor[1] + dy
    glyph_w, glyph_h = reader.glyph_size
    if (x < 0 or y < 0 or x + glyph_w * reader.slots > image.width
            or y + glyph_h > image.height):
        return None
    crop = image.convert("RGB").crop((x, y, x + glyph_w * reader.slots,
                                       y + glyph_h))
    digits, confidence = [], []
    for slot in range(reader.slots):
        cell = crop.crop((slot * glyph_w, 0, (slot + 1) * glyph_w, glyph_h))
        pixels = np.asarray(cell)
        scores = []
        for template, mask in reader.templates:
            same = np.all(pixels == template, axis=2)
            scores.append(float(np.count_nonzero(same & mask)) /
                          int(np.count_nonzero(mask)))
        order = sorted(range(10), key=lambda idx: scores[idx], reverse=True)
        best, second = order[:2]
        if scores[best] < reader.minimum_score:
            digits.append(None)
        elif scores[best] - scores[second] < reader.minimum_margin:
            return None
        else:
            digits.append(best)
            confidence.append(scores[best])
    first = next((i for i, digit in enumerate(digits) if digit is not None), None)
    if (first is None or any(value is None for value in digits[first:])
            or any(value is not None for value in digits[:first])):
        return None
    return {"dx": dx, "dy": dy,
            "value": int("".join(str(value) for value in digits[first:])),
            "mean_score": sum(confidence) / len(confidence)}


def independent_decision(reader, observation, image, exact, offsets):
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
        hit = independent_classify(reader, image, observation, dx, dy)
        if hit is not None:
            matches.append(hit)
    values = sorted({match["value"] for match in matches})
    if len(values) == 0:
        return {"status": "unknown", "value": None,
                "reason": "no_complete_anchor_match", "candidate_values": [],
                "source": "offset_search", "chosen_offset": None,
                "matching_offset_count": 0}
    if len(values) > 1:
        return {"status": "unknown", "value": None,
                "reason": "conflicting_anchor_values", "candidate_values": values,
                "source": "offset_search", "chosen_offset": None,
                "matching_offset_count": len(matches)}
    selected = sorted(matches, key=lambda match: (
        -match["mean_score"], abs(match["dx"]) + abs(match["dy"]),
        abs(match["dy"]), abs(match["dx"])))[0]
    return {"status": "observed", "value": values[0], "reason": None,
            "candidate_values": values, "source": "offset_search",
            "chosen_offset": {"dx": selected["dx"], "dy": selected["dy"]},
            "matching_offset_count": len(matches)}


def blank_roi(frame, binding):
    output = frame.convert("RGB").copy()
    x = binding["geometry"][0] + FREEZE["health_local_anchor"][0]
    y = binding["geometry"][1] + FREEZE["health_local_anchor"][1]
    width, height = FREEZE["glyph_size"]
    ImageDraw.Draw(output).rectangle(
        (x, y, x + width * FREEZE["slots"] - 1, y + height - 1), fill=(0, 0, 0))
    return output


def build_expected(repo, wad_path):
    base = FREEZE["base_commit"]
    source_bytes = blob(repo, base, FREEZE["source_freeze_path"])
    source = json.loads(source_bytes)
    with tempfile.TemporaryDirectory(prefix="hud-diagonal-a04-audit-") as temp:
        module_root = Path(temp)
        for path in FREEZE["reader_blobs"]:
            (module_root / Path(path).name).write_bytes(blob(repo, base, path))
        sys.path.insert(0, str(module_root))
        module = importlib.import_module("doom_hud_signal_v3")
        reader = module.DoomStatusNumberReader(
            wad_path, signal_id="health", expected_wad_sha256=FREEZE["wad_sha256"])
        rows, blanks = [], []
        axis = [tuple(pair) for pair in FREEZE["axis_offsets"]]
        square = [tuple(pair) for pair in FREEZE["square_offsets"]]
        for meta in source["frames"]:
            frame_bytes = blob(repo, base, meta["frame_path"])
            with Image.open(io.BytesIO(frame_bytes)) as opened:
                original = opened.convert("RGB")
            observation = {"sequence": meta["sequence"], "capture_ns": meta["capture_ns"],
                           "pointer_binding": meta["pointer_binding"]}
            truth = source["manual_health"][meta["index"]]
            cases = [("baseline", 0, 0, original)]
            cases.extend(("diagonal", dx, dy, shifted(original, dx, dy))
                         for dx, dy in FREEZE["diagonal_translations"])
            for case_index, (variant, dx, dy, image) in enumerate(cases):
                exact = reader.read_frame(observation, image)
                order = ["axis", "square"] if case_index % 2 == 0 else ["square", "axis"]
                rows.append({
                    "frame_index": meta["index"], "frame_path": meta["frame_path"],
                    "source_png_sha256": meta["sha256"], "expected_health": truth,
                    "variant": variant, "translation": {"dx": dx, "dy": dy},
                    "transformed_rgb_sha256": rgb_digest(image),
                    "exact": {"status": exact.get("status"), "value": exact.get("value"),
                              "reason": exact.get("reason")},
                    "arm_order": order,
                    "axis": independent_decision(reader, observation, image, exact, axis),
                    "square": independent_decision(reader, observation, image, exact, square),
                })
            blank = blank_roi(original, meta["pointer_binding"])
            exact = reader.read_frame(observation, blank)
            order = ["axis", "square"] if meta["index"] % 2 == 0 else ["square", "axis"]
            blanks.append({
                "frame_index": meta["index"], "transformed_rgb_sha256": rgb_digest(blank),
                "exact": {"status": exact.get("status"), "value": exact.get("value"),
                          "reason": exact.get("reason")},
                "arm_order": order,
                "axis": independent_decision(reader, observation, blank, exact, axis),
                "square": independent_decision(reader, observation, blank, exact, square),
            })
    baseline = [row for row in rows if row["variant"] == "baseline"]
    diagonal = [row for row in rows if row["variant"] == "diagonal"]
    summary = {"frame_count": len(baseline), "diagonal_count": len(diagonal)}
    for arm in ("axis", "square"):
        summary[arm] = {
            "baseline_correct": sum(row[arm]["status"] == "observed" and
                                     row[arm]["value"] == row["expected_health"] for row in baseline),
            "diagonal_correct": sum(row[arm]["status"] == "observed" and
                                     row[arm]["value"] == row["expected_health"] for row in diagonal),
            "diagonal_wrong_observed": sum(row[arm]["status"] == "observed" and
                                            row[arm]["value"] != row["expected_health"] for row in diagonal),
            "diagonal_unknown": sum(row[arm]["status"] == "unknown" for row in diagonal),
        }
    summary["blank_controls"] = len(blanks)
    summary["axis_blank_unknown"] = sum(row["axis"]["status"] == "unknown" for row in blanks)
    summary["square_blank_unknown"] = sum(row["square"]["status"] == "unknown" for row in blanks)
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
    return rows, blanks, summary


def compare(result, expected, candidate_hash, auditor_hash, freeze_hash, wad_hash):
    rows, blanks, summary = expected
    errors = []
    metadata = {
        "schema": "v39-hud-anchor-diagonal-a04-v1",
        "execution_id": FREEZE["execution_id"],
        "base_commit": FREEZE["base_commit"],
        "source_freeze_sha256": FREEZE["source_freeze_sha256"],
        "reader_blobs": FREEZE["reader_blobs"],
        "wad_sha256": wad_hash,
        "candidate_sha256": candidate_hash,
        "auditor_sha256": auditor_hash,
        "freeze_sha256": freeze_hash,
        "offsets": {"axis": FREEZE["axis_offsets"],
                    "square": FREEZE["square_offsets"],
                    "tested_diagonals": FREEZE["diagonal_translations"]},
        "runtime": {"python": FREEZE["runtime_versions"]["python"],
                    "numpy": FREEZE["runtime_versions"]["numpy"],
                    "pillow": FREEZE["runtime_versions"]["pillow"],
                    "platform": sys.platform, "gui_or_game_launched": False,
                    "model_calls": 0, "os_input_emitted": False},
    }
    for key, value in metadata.items():
        if result.get(key) != value:
            errors.append(f"metadata:{key}")
    actual_rows = result.get("rows") if type(result.get("rows")) is list else []
    if len(actual_rows) != len(rows):
        errors.append("row count")
    for index, (actual, wanted) in enumerate(zip(actual_rows, rows)):
        for key in ("frame_index", "frame_path", "source_png_sha256", "expected_health",
                    "variant", "translation", "transformed_rgb_sha256", "exact", "arm_order"):
            if actual.get(key) != wanted.get(key):
                errors.append(f"row {index}:{key}")
        for arm in ("axis", "square"):
            observed_arm = actual.get(arm) if type(actual.get(arm)) is dict else {}
            for key, value in wanted[arm].items():
                if observed_arm.get(key) != value:
                    errors.append(f"row {index}:{arm}:{key}")
            elapsed = observed_arm.get("elapsed_ns")
            if type(elapsed) is not int or elapsed <= 0:
                errors.append(f"row {index}:{arm}:elapsed_ns")
    actual_blanks = result.get("blank_rows") if type(result.get("blank_rows")) is list else []
    if len(actual_blanks) != len(blanks):
        errors.append("blank count")
    for index, (actual, wanted) in enumerate(zip(actual_blanks, blanks)):
        for key in ("frame_index", "transformed_rgb_sha256", "exact", "arm_order"):
            if actual.get(key) != wanted.get(key):
                errors.append(f"blank {index}:{key}")
        for arm in ("axis", "square"):
            observed_arm = actual.get(arm) if type(actual.get(arm)) is dict else {}
            for key, value in wanted[arm].items():
                if observed_arm.get(key) != value:
                    errors.append(f"blank {index}:{arm}:{key}")
            elapsed = observed_arm.get("elapsed_ns")
            if type(elapsed) is not int or elapsed <= 0:
                errors.append(f"blank {index}:{arm}:elapsed_ns")
    actual_summary = copy.deepcopy(summary)
    for arm in ("axis", "square"):
        samples = sorted(row[arm]["elapsed_ns"] for row in actual_rows
                         if type(row.get(arm)) is dict and
                         type(row[arm].get("elapsed_ns")) is int and row[arm]["elapsed_ns"] > 0)
        if samples:
            actual_summary[arm]["timing_ns"] = {
                "n": len(samples), "median": statistics.median(samples),
                "p95_nearest_rank": samples[math.ceil(0.95 * len(samples)) - 1],
                "max": max(samples),
            }
    if result.get("summary") != actual_summary:
        errors.append("summary")
    return errors


def main():
    repo = HERE.parents[3]
    result_path = HERE / "results" / "a04.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    wad_path = Path(sys.argv[1]).resolve()
    wad_hash = digest(wad_path.read_bytes())
    errors = []
    if wad_hash != FREEZE["wad_sha256"]:
        errors.append("WAD SHA-256")
    if digest((HERE / "candidate_a04.py").read_bytes()) != FREEZE["candidate_sha256"]:
        errors.append("candidate source SHA-256")
    if digest(Path(__file__).read_bytes()) != FREEZE["auditor_sha256"]:
        errors.append("auditor source SHA-256")
    source_bytes = blob(repo, FREEZE["base_commit"], FREEZE["source_freeze_path"])
    if digest(source_bytes) != FREEZE["source_freeze_sha256"]:
        errors.append("source freeze SHA-256")
    for path, expected_blob in FREEZE["reader_blobs"].items():
        actual = subprocess.check_output(["git", "rev-parse", f"{FREEZE['base_commit']}:{path}"],
                                         cwd=repo, text=True).strip()
        if actual != expected_blob:
            errors.append(f"reader blob:{path}")
    prior_result_bytes = blob(repo, FREEZE["base_commit"], FREEZE["prior_a03_result_path"])
    prior_audit_bytes = blob(repo, FREEZE["base_commit"], FREEZE["prior_a03_audit_path"])
    if digest(prior_result_bytes) != FREEZE["prior_a03_result_sha256"]:
        errors.append("A03 result SHA-256")
    if digest(prior_audit_bytes) != FREEZE["prior_a03_audit_sha256"]:
        errors.append("A03 audit SHA-256")
    if json.loads(prior_result_bytes).get("status") != "PASS_BOUNDED_CROSS_SEARCH":
        errors.append("A03 result disposition")
    if (json.loads(prior_audit_bytes).get("errors") != []
            or json.loads(prior_audit_bytes).get("mutation_controls_passed") != 5):
        errors.append("A03 audit disposition")
    if not errors:
        expected = build_expected(repo, wad_path)
        errors.extend(compare(
            result, expected, FREEZE["candidate_sha256"], FREEZE["auditor_sha256"],
            digest((HERE / "FREEZE_A04.json").read_bytes()), wad_hash))
    else:
        expected = ([], [], {})

    mutations = []
    if not errors:
        cases = []
        changed = copy.deepcopy(result)
        changed["rows"][0]["square"]["value"] = -999
        cases.append(changed)
        changed = copy.deepcopy(result)
        changed["rows"][-1]["axis"]["status"] = "observed"
        cases.append(changed)
        changed = copy.deepcopy(result)
        changed["blank_rows"][0]["square"]["status"] = "observed"
        cases.append(changed)
        changed = copy.deepcopy(result)
        changed["summary"]["square"]["diagonal_correct"] += 1
        cases.append(changed)
        changed = copy.deepcopy(result)
        changed["reader_blobs"][next(iter(changed["reader_blobs"]))] = "0" * 40
        cases.append(changed)
        mutations = [bool(compare(
            case, expected, FREEZE["candidate_sha256"], FREEZE["auditor_sha256"],
            digest((HERE / "FREEZE_A04.json").read_bytes()), wad_hash)) for case in cases]
        if not all(mutations):
            errors.append("mutation controls")

    audit = {
        "schema": "v39-hud-anchor-diagonal-a04-audit-v1",
        "status": "PASS_AUDIT" if not errors else "FAIL_AUDIT",
        "errors": errors,
        "mutation_controls_passed": sum(mutations),
        "mutation_controls_total": len(mutations),
        "independently_reconstructed_summary": expected[2],
        "scope": "retained pixels plus fixed synthetic diagonal translations; no live-control claim",
    }
    output = HERE / "results" / "audit_a04.json"
    output.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
