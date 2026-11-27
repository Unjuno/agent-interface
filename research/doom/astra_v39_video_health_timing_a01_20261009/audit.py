"""Independent scalar recheck of the post-hoc video health timeline."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

PACKAGE = Path(__file__).resolve().parent
FREEZE = json.loads((PACKAGE / "FREEZE.json").read_text(encoding="utf-8"))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob(repo: Path, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{FREEZE['base_commit']}:{path}"], cwd=repo)


def read_wad_templates(data: bytes):
    expected = FREEZE["wad_sha256"]
    if sha(data) != expected:
        raise ValueError("WAD hash mismatch")
    ident, count, directory = struct.unpack_from("<4sII", data, 0)
    if ident not in (b"IWAD", b"PWAD") or directory + count * 16 > len(data):
        raise ValueError("bad WAD directory")
    lumps = {}
    for index in range(count):
        offset, size, name = struct.unpack_from("<II8s", data, directory + index * 16)
        if offset + size > len(data):
            raise ValueError("bad WAD lump bounds")
        lumps[name.rstrip(b"\0").decode("ascii")] = data[offset:offset + size]
    palette = np.frombuffer(lumps["PLAYPAL"][:768], dtype=np.uint8).reshape(256, 3)
    templates = []
    for digit in range(10):
        patch = lumps[f"STTNUM{digit}"]
        width, height, _, _ = struct.unpack_from("<hhhh", patch, 0)
        indices = np.zeros((height, width), dtype=np.uint8)
        alpha = np.zeros((height, width), dtype=np.uint8)
        for x in range(width):
            cursor = struct.unpack_from("<I", patch, 8 + 4 * x)[0]
            while True:
                top = patch[cursor]
                if top == 255:
                    break
                length = patch[cursor + 1]
                start = cursor + 3
                indices[top:top + length, x] = np.frombuffer(patch[start:start + length], dtype=np.uint8)
                alpha[top:top + length, x] = 255
                cursor = start + length + 1
        rgba = np.dstack((palette[indices], alpha))
        rendered = np.asarray(Image.fromarray(rgba).resize(
            tuple(FREEZE["glyph_size"]), Image.Resampling.NEAREST))
        templates.append((rendered[:, :, :3], rendered[:, :, 3] > 0))
    return templates


def scalar_health(frame: np.ndarray, templates):
    x0, y0 = FREEZE["video_game_origin"]
    gx, gy = FREEZE["health_local_anchor"]
    gw, gh = FREEZE["glyph_size"]
    slots = []
    digits = []
    for slot in range(3):
        crop = frame[y0 + gy:y0 + gy + gh, x0 + gx + slot * gw:x0 + gx + (slot + 1) * gw]
        scores = []
        for template, mask in templates:
            matched = total = 0
            for y in range(gh):
                for x in range(gw):
                    if mask[y, x]:
                        total += 1
                        if all(abs(int(crop[y, x, c]) - int(template[y, x, c])) <=
                               FREEZE["channel_tolerance"] for c in range(3)):
                            matched += 1
            scores.append(matched / total)
        order = sorted(range(10), key=scores.__getitem__, reverse=True)
        best, second = order[:2]
        score, margin = scores[best], scores[best] - scores[second]
        if score < FREEZE["blank_score_below"]:
            digit, state = None, "blank"
        elif score < FREEZE["minimum_score"] or margin < FREEZE["minimum_margin"]:
            digit, state = None, "uncertain"
        else:
            digit, state = best, "digit"
        slots.append({"slot": slot, "state": state, "digit": digit, "best_digit": best,
                      "best_score": score, "second_score": scores[second], "margin": margin})
        digits.append(digit)
    first = next((index for index, digit in enumerate(digits) if digit is not None), None)
    if first is None or any(digit is None for digit in digits[first:]) or any(
            digit is not None for digit in digits[:first]):
        return {"status": "unknown", "value": None, "reason": "invalid_right_aligned_number", "slots": slots}
    return {"status": "observed", "value": int("".join(str(digit) for digit in digits[first:])),
            "reason": None, "slots": slots}


def scalar_anchor_score(frame: np.ndarray, source: Image.Image) -> float:
    width, height = FREEZE["video_size"]
    x0, y0 = FREEZE["video_game_origin"]
    left = Image.fromarray(frame[y0:y0 + 400, x0:x0 + 640]).resize((160, 100), Image.Resampling.BOX)
    sx, sy, _, _ = FREEZE["source_frame_geometry"]
    right = source.crop((sx, sy, sx + 640, sy + 400)).resize((160, 100), Image.Resampling.BOX)
    a, b = np.asarray(left).astype(np.int16), np.asarray(right).astype(np.int16)
    return float(np.abs(a[:FREEZE["anchor_score_rows"]] - b[:FREEZE["anchor_score_rows"]]).sum(dtype=np.int64) /
                 (FREEZE["anchor_score_rows"] * 160 * 3))


def output_valid(result: dict) -> bool:
    rows = result.get("rows", [])
    first, last = FREEZE["video_frame_range"]
    if len(rows) != last - first:
        return False
    if [r.get("video_frame_index") for r in rows] != list(range(first, last)):
        return False
    if result.get("model_call", {}).get("start_ns") != FREEZE["model_start_ns"]:
        return False
    if result.get("model_call", {}).get("end_ns") != FREEZE["model_end_ns"]:
        return False
    if len(result.get("clock_anchors", [])) != len(FREEZE["anchor_source_frames"]):
        return False
    observed_unknowns = sum(r.get("health_status") != "observed" for r in rows)
    if result.get("health_reader", {}).get("unknown_count") != observed_unknowns:
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--git-root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--wad", type=Path, required=True)
    args = parser.parse_args()
    repo = args.git_root.resolve()
    result_path = PACKAGE / "results" / "candidate.json"
    result_bytes = result_path.read_bytes()
    freeze_sha256 = sha((PACKAGE / "FREEZE.json").read_bytes())
    result = json.loads(result_bytes)
    failures = []
    def check(condition, label):
        if not condition:
            failures.append(label)

    check(sha(Path(__file__).read_bytes()) == FREEZE["auditor_sha256"], "auditor hash")
    check(sha((PACKAGE / "candidate.py").read_bytes()) == FREEZE["candidate_sha256"], "candidate hash")
    check(result.get("freeze_sha256") == freeze_sha256, "freeze hash")
    check(result.get("execution_id") == FREEZE["execution_id"], "execution id")
    check(result.get("base_commit") == FREEZE["base_commit"], "base commit")
    check(output_valid(result), "candidate output structure")
    wad = args.wad.resolve().read_bytes()
    templates = read_wad_templates(wad)
    report_bytes = git_blob(repo, FREEZE["report_path"])
    video_bytes = git_blob(repo, FREEZE["video_path"])
    source_freeze_bytes = git_blob(repo, FREEZE["source_freeze_path"])
    check(sha(video_bytes) == FREEZE["video_sha256"], "video source hash")
    check(sha(git_blob(repo, FREEZE["events_path"])) == FREEZE["events_sha256"], "event source hash")
    check(sha(report_bytes) == FREEZE["report_sha256"], "report source hash")
    check(sha(source_freeze_bytes) == FREEZE["source_freeze_sha256"], "source freeze hash")
    report = json.loads(report_bytes)
    decision = report["decisions"][FREEZE["model_decision_index"]]
    check(decision["controller_model_started_ns"] == FREEZE["model_start_ns"], "model start identity")
    check(decision["controller_model_ended_ns"] == FREEZE["model_end_ns"], "model end identity")
    check(decision["model_ns"] == FREEZE["reported_model_ns"], "reported model duration")
    source_freeze = json.loads(source_freeze_bytes)
    source_images = []
    for anchor in FREEZE["anchor_source_frames"]:
        meta = source_freeze["frames"][anchor["freeze_frame_index"]]
        blob = git_blob(repo, meta["frame_path"])
        check(sha(blob) == meta["sha256"], f"source frame {anchor['freeze_frame_index']} hash")
        source_images.append(Image.open(io.BytesIO(blob)).convert("RGB"))

    ffmpeg_version = subprocess.check_output([FREEZE["ffmpeg_path"], "-version"], text=True).splitlines()[0]
    check(ffmpeg_version == FREEZE["ffmpeg_version"], "ffmpeg identity")
    with tempfile.TemporaryDirectory(prefix="astra-video-audit-") as temporary:
        video_path = Path(temporary) / "input.mp4"
        video_path.write_bytes(video_bytes)
        command = [FREEZE["ffmpeg_path"], "-hide_banner", "-loglevel", "error", "-i", str(video_path),
                   "-f", "rawvideo", "-pix_fmt", "rgb24", "-vsync", "0", "-"]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert process.stdout is not None
        width, height = FREEZE["video_size"]
        frame_size = width * height * 3
        first, last = FREEZE["video_frame_range"]
        independent_rows = []
        anchor_scores = [[] for _ in source_images]
        frame_count = 0
        while True:
            raw = process.stdout.read(frame_size)
            if not raw:
                break
            if len(raw) != frame_size:
                check(False, "independent decoded frame alignment")
                break
            frame = np.frombuffer(raw, dtype=np.uint8).reshape(height, width, 3)
            for i, source in enumerate(source_images):
                anchor_scores[i].append((scalar_anchor_score(frame, source), frame_count))
            if first <= frame_count < last:
                parsed = scalar_health(frame, templates)
                independent_rows.append({"ordinal": frame_count - first,
                                         "video_frame_index": frame_count,
                                         "video_seconds": frame_count / FREEZE["video_fps"],
                                         "frame_rgb_sha256": sha(width.to_bytes(4, "big") +
                                                                  height.to_bytes(4, "big") + raw),
                                         "health_status": parsed["status"],
                                         "health_value": parsed["value"],
                                         "health_reason": parsed.get("reason"),
                                         "slots": parsed.get("slots")})
            frame_count += 1
        stderr = process.stderr.read() if process.stderr else b""
        return_code = process.wait()
        check(return_code == 0, "independent ffmpeg decode")
    check(len(stderr) == 0, "independent decoder stderr")
    check(frame_count == FREEZE["video_frame_count"], "decoded frame count")
    candidate_rows = result.get("rows", [])
    check(len(candidate_rows) == len(independent_rows), "independent row count")
    row_mismatches = []
    for expected, actual in zip(independent_rows, candidate_rows):
        if (expected["video_frame_index"] != actual.get("video_frame_index") or
                expected["frame_rgb_sha256"] != actual.get("frame_rgb_sha256") or
                expected["health_status"] != actual.get("health_status") or
                expected["health_value"] != actual.get("health_value") or
                expected["health_reason"] != actual.get("health_reason")):
            row_mismatches.append(expected["video_frame_index"])
            continue
        for expected_slot, actual_slot in zip(expected["slots"] or [], actual.get("slots") or []):
            if any(expected_slot.get(k) != actual_slot.get(k) for k in ("slot", "state", "digit", "best_digit")):
                row_mismatches.append(expected["video_frame_index"])
                break
            if any(abs(expected_slot[k] - actual_slot[k]) > 1e-12 for k in ("best_score", "second_score", "margin")):
                row_mismatches.append(expected["video_frame_index"])
                break
    check(not row_mismatches, "independent HUD rows")

    independent_anchors = []
    for anchor, metadata, scores in zip(FREEZE["anchor_source_frames"],
                                        FREEZE["source_frame_metadata"], anchor_scores):
        scores.sort()
        best_score, best_index = scores[0]
        close = [(score, index) for score, index in scores
                 if score <= best_score + FREEZE["anchor_ambiguity_margin"]]
        local = [(score, index) for score, index in close
                 if abs(index - best_index) <= FREEZE["anchor_local_radius_frames"]]
        aliases = [(score, index) for score, index in close
                   if abs(index - best_index) > FREEZE["anchor_local_radius_frames"]]
        local.sort(key=lambda item: item[1])
        aliases.sort(key=lambda item: item[1])
        independent_anchors.append({"source_frame_index": anchor["freeze_frame_index"],
                                    "sequence": metadata["sequence"],
                                    "source_capture_ns": metadata["capture_ns"],
                                    "source_png_sha256": metadata["sha256"], "best_score": best_score,
                                    "best_video_frame_indices": [i for _, i in local],
                                    "best_video_seconds": [i / FREEZE["video_fps"] for _, i in local],
                                    "alias_video_frame_indices": [i for _, i in aliases],
                                    "top_matches": [{"video_frame_index": i,
                                                     "video_seconds": i / FREEZE["video_fps"], "score": score}
                                                    for score, i in scores[:10]]})
    candidate_anchors = result.get("clock_anchors", [])
    check(len(candidate_anchors) == len(independent_anchors), "anchor count")
    anchor_mismatches = []
    for expected, actual in zip(independent_anchors, candidate_anchors):
        exact_fields = ("source_frame_index", "sequence", "source_capture_ns", "source_png_sha256",
                        "best_video_frame_indices", "best_video_seconds", "alias_video_frame_indices")
        if any(expected[k] != actual.get(k) for k in exact_fields):
            anchor_mismatches.append(expected["source_frame_index"])
        if abs(expected["best_score"] - actual.get("best_score", float("inf"))) > 1e-10:
            anchor_mismatches.append(expected["source_frame_index"])
        for a, b in zip(expected["top_matches"], actual.get("top_matches", [])):
            if a["video_frame_index"] != b.get("video_frame_index") or abs(a["score"] - b.get("score", 1e99)) > 1e-10:
                anchor_mismatches.append(expected["source_frame_index"])
    check(not anchor_mismatches, "independent anchor mapping")

    transitions = []
    prior = None
    for row in independent_rows:
        if row["health_status"] == "observed" and row["health_value"] != prior:
            transitions.append({"video_seconds": row["video_seconds"],
                                "video_frame_index": row["video_frame_index"],
                                "health_value": row["health_value"], "previous_health_value": prior})
            prior = row["health_value"]
    check(transitions == result.get("transitions"), "transition summary")

    def rows_match(candidate):
        actual_rows = candidate.get("rows", [])
        return len(actual_rows) == len(independent_rows) and all(
            expected["video_frame_index"] == actual.get("video_frame_index") and
            expected["health_status"] == actual.get("health_status") and
            expected["health_value"] == actual.get("health_value") and
            expected["frame_rgb_sha256"] == actual.get("frame_rgb_sha256")
            for expected, actual in zip(independent_rows, actual_rows))

    def anchors_match(candidate):
        actual_anchors = candidate.get("clock_anchors", [])
        return len(actual_anchors) == len(independent_anchors) and all(
            expected["best_video_frame_indices"] == actual.get("best_video_frame_indices") and
            abs(expected["best_score"] - actual.get("best_score", float("inf"))) <= 1e-10
            for expected, actual in zip(independent_anchors, actual_anchors))

    mutation_results = {}
    mutations = {
        "drop_row": lambda d: d["rows"].pop(),
        "wrong_health": lambda d: d["rows"][0].update(health_value=17),
        "wrong_clock": lambda d: d["model_call"].update(end_ns=0),
        "wrong_anchor": lambda d: d["clock_anchors"][0].update(best_video_frame_indices=[999]),
        "wrong_unknown_count": lambda d: d["health_reader"].update(unknown_count=999),
    }
    for name, mutate in mutations.items():
        changed = json.loads(json.dumps(result))
        mutate(changed)
        mutation_results[name] = (not anchors_match(changed) if name == "wrong_anchor" else
                                  not rows_match(changed) if name in ("drop_row", "wrong_health") else
                                  not output_valid(changed))
    check(all(mutation_results.values()), "auditor mutation controls")

    model_end_seconds = result["model_call"]["estimated_end_video_seconds"]
    fit_uncertainty = result["model_call"]["fit_uncertainty_seconds_only"]
    crossings = result.get("guard_floor_crossings_sensitivity_only", [])
    relation = []
    for crossing in crossings:
        sample_time = crossing.get("first_below_video_seconds")
        if sample_time is None:
            state = "NO_CROSSING_IN_WINDOW"
        elif abs(sample_time - model_end_seconds) <= fit_uncertainty + 1.0 / FREEZE["video_fps"]:
            state = "UNRESOLVED_WITHIN_FRAME_AND_FIT_WINDOW"
        elif sample_time < model_end_seconds:
            state = "SAMPLED_BELOW_BEFORE_ESTIMATED_CONTROLLER_END"
        else:
            state = "SAMPLED_BELOW_AFTER_ESTIMATED_CONTROLLER_END"
        relation.append({"floor": crossing["floor"], "sample_video_seconds": sample_time,
                         "controller_end_video_seconds": model_end_seconds,
                         "fit_uncertainty_seconds_only": fit_uncertainty,
                         "unmodeled_media_sync_uncertainty": "unknown", "ordering": state})
    audit = {"schema": "astra-video-health-timing-a01-audit-v1",
             "execution_id": FREEZE["execution_id"],
             "status": "PASS_AUDIT" if not failures else "FAIL_AUDIT",
             "candidate_result_sha256": sha(result_bytes), "candidate_sha256": FREEZE["candidate_sha256"],
             "auditor_sha256": FREEZE["auditor_sha256"], "freeze_sha256": freeze_sha256,
             "base_commit": FREEZE["base_commit"], "decoded_frame_count": frame_count,
             "recomputed_rows": len(independent_rows), "unknown_rows": sum(
                 row["health_status"] != "observed" for row in independent_rows),
             "row_mismatches": sorted(set(row_mismatches)),
             "anchor_mismatches": sorted(set(anchor_mismatches)),
             "mutation_controls": mutation_results,
             "threshold_timing_relation": relation,
             "model_duration_note": {"controller_elapsed_ns": FREEZE["model_end_ns"] - FREEZE["model_start_ns"],
                                     "report_model_ns": FREEZE["reported_model_ns"],
                                     "difference_ns": FREEZE["model_end_ns"] - FREEZE["model_start_ns"] -
                                                    FREEZE["reported_model_ns"],
                                     "interpretation": "Both values are retained; source does not explain the difference."},
             "failures": failures,
             "scope": "Independent offline audit only; historical video timing cannot establish what a current guard would have done."}
    output = PACKAGE / "results" / "audit.json"
    output.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": audit["status"], "failures": failures,
                      "rows": len(independent_rows), "mutations": mutation_results,
                      "threshold_timing_relation": relation}, sort_keys=True))
    return 0 if audit["status"] == "PASS_AUDIT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
