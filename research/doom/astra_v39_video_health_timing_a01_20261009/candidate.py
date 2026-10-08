"""Hash-bound, post-hoc HUD timeline extraction from the retained Astra video."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import io
import json
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


def git_blob(repo: Path, commit: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=repo)


def frame_rgb_digest(raw: bytes, width: int, height: int) -> str:
    return sha(width.to_bytes(4, "big") + height.to_bytes(4, "big") + raw)


def classify_health(raw: bytes, reader, width: int, height: int):
    frame = np.frombuffer(raw, dtype=np.uint8).reshape((height, width, 3))
    x0, y0 = FREEZE["video_game_origin"]
    left = x0 + reader.local_anchor[0]
    top = y0 + reader.local_anchor[1]
    glyph_width, glyph_height = reader.glyph_size
    pixels = frame[top:top + glyph_height, left:left + glyph_width * reader.slots]
    if pixels.shape != (glyph_height, glyph_width * reader.slots, 3):
        return {"status": "unknown", "value": None, "reason": "health_roi_outside_video"}
    slots = []
    digits = []
    for slot in range(reader.slots):
        crop = pixels[:, slot * glyph_width:(slot + 1) * glyph_width]
        scores = []
        for template, mask in reader.templates:
            delta = np.abs(crop.astype(np.int16) - template.astype(np.int16))
            scores.append(float(np.all(delta <= FREEZE["channel_tolerance"], axis=2)[mask].mean()))
        order = sorted(range(10), key=scores.__getitem__, reverse=True)
        best, second = order[:2]
        top_score, margin = scores[best], scores[best] - scores[second]
        if top_score < FREEZE["blank_score_below"]:
            digit, state = None, "blank"
        elif top_score < FREEZE["minimum_score"] or margin < FREEZE["minimum_margin"]:
            digit, state = None, "uncertain"
        else:
            digit, state = best, "digit"
        slots.append({"slot": slot, "state": state, "digit": digit, "best_digit": best,
                      "best_score": top_score, "second_score": scores[second], "margin": margin})
        digits.append(digit)
    first = next((index for index, digit in enumerate(digits) if digit is not None), None)
    if first is None or any(digit is None for digit in digits[first:]) or any(
            digit is not None for digit in digits[:first]):
        return {"status": "unknown", "value": None,
                "reason": "invalid_right_aligned_number", "slots": slots}
    return {"status": "observed", "value": int("".join(str(digit) for digit in digits[first:])),
            "reason": None, "slots": slots}


def anchor_score(video_raw: bytes, source: Image.Image) -> float:
    width, height = FREEZE["video_size"]
    video = np.frombuffer(video_raw, dtype=np.uint8).reshape((height, width, 3))
    x0, y0 = FREEZE["video_game_origin"]
    video_crop = Image.fromarray(video[y0:y0 + 400, x0:x0 + 640]).resize(
        (160, 100), Image.Resampling.BOX)
    sx, sy, _, _ = FREEZE["source_frame_geometry"]
    source_crop = source.crop((sx, sy, sx + 640, sy + 400)).resize(
        (160, 100), Image.Resampling.BOX)
    left = np.asarray(video_crop).astype(np.int16)
    right = np.asarray(source_crop).astype(np.int16)
    return float(np.abs(left[:FREEZE["anchor_score_rows"]] -
                        right[:FREEZE["anchor_score_rows"]]).mean())


def decode_video(video_path: Path, expected_frames: int, reader, source_images):
    width, height = FREEZE["video_size"]
    frame_bytes = width * height * 3
    command = [FREEZE["ffmpeg_path"], "-hide_banner", "-loglevel", "error", "-i",
               str(video_path), "-f", "rawvideo", "-pix_fmt", "rgb24", "-vsync", "0", "-"]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert process.stdout is not None
    first_index, last_index = FREEZE["video_frame_range"]
    source_images = [Image.open(io.BytesIO(raw)).convert("RGB") for raw in source_images]
    anchor_candidates = [[] for _ in source_images]
    rows = []
    video_index = 0
    while True:
        raw = process.stdout.read(frame_bytes)
        if not raw:
            break
        if len(raw) != frame_bytes:
            raise RuntimeError(f"partial decoded frame: {len(raw)} bytes")
        for anchor_index, source in enumerate(source_images):
            anchor_candidates[anchor_index].append((anchor_score(raw, source), video_index))
        if first_index <= video_index < last_index:
            parsed = classify_health(raw, reader, width, height)
            rows.append({"ordinal": video_index - first_index, "video_frame_index": video_index,
                         "video_seconds": video_index / FREEZE["video_fps"],
                         "frame_rgb_sha256": frame_rgb_digest(raw, width, height),
                         "health_status": parsed["status"], "health_value": parsed["value"],
                         "health_reason": parsed.get("reason"), "slots": parsed.get("slots")})
        video_index += 1
    stderr = process.stderr.read() if process.stderr else b""
    exit_code = process.wait()
    if exit_code != 0:
        raise RuntimeError(f"ffmpeg exited {exit_code}: {stderr.decode('utf-8', 'replace')}")
    if video_index != expected_frames:
        raise RuntimeError(f"decoded frame count {video_index} != frozen {expected_frames}")
    if len(rows) != last_index - first_index:
        raise RuntimeError(f"selected row count {len(rows)} != frozen range")
    anchors = []
    radius = FREEZE["anchor_local_radius_frames"]
    for anchor, frame_meta, candidates in zip(FREEZE["anchor_source_frames"],
                                               FREEZE["source_frame_metadata"], anchor_candidates):
        candidates.sort()
        best_score, best_index = candidates[0]
        close = [(score, index) for score, index in candidates
                 if score <= best_score + FREEZE["anchor_ambiguity_margin"]]
        local = [(score, index) for score, index in close if abs(index - best_index) <= radius]
        aliases = [(score, index) for score, index in close if abs(index - best_index) > radius]
        local.sort(key=lambda item: item[1])
        aliases.sort(key=lambda item: item[1])
        anchors.append({"source_frame_index": anchor["freeze_frame_index"],
                        "sequence": frame_meta["sequence"], "source_capture_ns": frame_meta["capture_ns"],
                        "source_png_sha256": frame_meta["sha256"], "best_score": best_score,
                        "best_video_frame_indices": [index for _, index in local],
                        "best_video_seconds": [index / FREEZE["video_fps"] for _, index in local],
                        "alias_video_frame_indices": [index for _, index in aliases],
                        "top_matches": [{"video_frame_index": index,
                                         "video_seconds": index / FREEZE["video_fps"], "score": score}
                                        for score, index in candidates[:10]]})
    return rows, anchors, sha(stderr), video_index


def threshold_crossings(rows: list[dict]) -> list[dict]:
    crossings = []
    for floor in FREEZE["guard_floor_sweep"]:
        prior = None
        crossing = None
        for row in rows:
            if row["health_status"] != "observed":
                continue
            value = row["health_value"]
            if value < floor:
                crossing = {"floor": floor,
                            "previous_video_seconds": None if prior is None else prior["video_seconds"],
                            "first_below_video_seconds": row["video_seconds"],
                            "health_value": value,
                            "previous_health_value": None if prior is None else prior["health_value"],
                            "video_frame_index": row["video_frame_index"]}
                break
            prior = row
        crossings.append(crossing or {"floor": floor, "first_below_video_seconds": None})
    return crossings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--git-root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--wad", type=Path, required=True)
    args = parser.parse_args()
    repo = args.git_root.resolve()
    if sha(Path(__file__).read_bytes()) != FREEZE["candidate_sha256"] or sha(
            (PACKAGE / "audit.py").read_bytes()) != FREEZE["auditor_sha256"]:
        raise SystemExit("HOLD_CODE_HASH")
    wad_bytes = args.wad.resolve().read_bytes()
    if sha(wad_bytes) != FREEZE["wad_sha256"]:
        raise SystemExit("HOLD_WAD_HASH")
    input_fields = ("video_sha256", "events_sha256", "report_sha256", "source_freeze_sha256")
    input_bytes = {field: git_blob(repo, FREEZE["base_commit"], FREEZE[path_field])
                   for field, path_field in (("video_sha256", "video_path"),
                                             ("events_sha256", "events_path"),
                                             ("report_sha256", "report_path"),
                                             ("source_freeze_sha256", "source_freeze_path"))}
    for field in input_fields:
        if sha(input_bytes[field]) != FREEZE[field]:
            raise SystemExit(f"HOLD_INPUT_HASH:{field}")
    runtime = {"python": sys.version.split()[0], "pillow": __import__("PIL").__version__,
               "numpy": np.__version__}
    if runtime != FREEZE["runtime_versions"]:
        raise SystemExit("HOLD_RUNTIME_VERSION")
    report = json.loads(input_bytes["report_sha256"])
    events = [json.loads(line) for line in input_bytes["events_sha256"].splitlines()]
    source_freeze = json.loads(input_bytes["source_freeze_sha256"])
    decision = report["decisions"][FREEZE["model_decision_index"]]
    if (decision["controller_model_started_ns"] != FREEZE["model_start_ns"] or
            decision["controller_model_ended_ns"] != FREEZE["model_end_ns"] or
            decision["model_ns"] != FREEZE["reported_model_ns"] or
            decision["model_session_id"] != FREEZE["model_session_id"]):
        raise SystemExit("HOLD_MODEL_TIME_IDENTITY")
    if len(events) != FREEZE["event_count"]:
        raise SystemExit("HOLD_EVENT_COUNT")
    source_frame_bytes = []
    for anchor in FREEZE["anchor_source_frames"]:
        frame = source_freeze["frames"][anchor["freeze_frame_index"]]
        blob = git_blob(repo, FREEZE["base_commit"], frame["frame_path"])
        if sha(blob) != frame["sha256"]:
            raise SystemExit(f"HOLD_SOURCE_FRAME:{frame['frame_path']}")
        source_frame_bytes.append(blob)
    ffmpeg_version = subprocess.check_output([FREEZE["ffmpeg_path"], "-version"], text=True).splitlines()[0]
    if ffmpeg_version != FREEZE["ffmpeg_version"]:
        raise SystemExit("HOLD_FFMPEG_VERSION")
    with tempfile.TemporaryDirectory(prefix="astra-video-health-") as temp:
        video_file = Path(temp) / "input.mp4"
        video_file.write_bytes(input_bytes["video_sha256"])
        module_root = Path(temp) / "modules"
        module_root.mkdir()
        for path in FREEZE["reader_modules"]:
            (module_root / Path(path).name).write_bytes(git_blob(repo, FREEZE["base_commit"], path))
        sys.path.insert(0, str(module_root))
        module = importlib.import_module("doom_hud_signal_v3")
        reader = module.DoomStatusNumberReader(args.wad, signal_id="health")
        rows, anchors, decoder_stderr_sha256, decoded_count = decode_video(
            video_file, FREEZE["video_frame_count"], reader, source_frame_bytes)
    capture_times = np.asarray([a["source_capture_ns"] for a in anchors], dtype=float)
    video_times = np.asarray([a["best_video_seconds"][len(a["best_video_seconds"]) // 2]
                              for a in anchors], dtype=float)
    if any(not a["best_video_seconds"] for a in anchors) or any(
            right <= left for left, right in zip(video_times, video_times[1:])):
        raise SystemExit("HOLD_ANCHOR_ORDER_OR_MATCH")
    slope, intercept = np.polyfit(video_times, capture_times, 1)
    if slope <= 0:
        raise SystemExit("HOLD_NONMONOTONIC_CLOCK_FIT")
    residual_seconds = ((capture_times - (slope * video_times + intercept)) / slope).tolist()
    model_start_video = (FREEZE["model_start_ns"] - intercept) / slope
    model_end_video = (FREEZE["model_end_ns"] - intercept) / slope
    max_anchor_halfwidth = max((max(a["best_video_seconds"]) - min(a["best_video_seconds"])) / 2
                               for a in anchors)
    fit_uncertainty = (max(abs(v) for v in residual_seconds) +
                       0.5 / FREEZE["video_fps"] + max_anchor_halfwidth)
    crossings = threshold_crossings(rows)
    unknown = sum(row["health_status"] != "observed" for row in rows)
    transitions = []
    previous = None
    for row in rows:
        if row["health_status"] == "observed" and row["health_value"] != previous:
            transitions.append({"video_seconds": row["video_seconds"],
                                "video_frame_index": row["video_frame_index"],
                                "health_value": row["health_value"],
                                "previous_health_value": previous})
            previous = row["health_value"]
    alias_count = sum(len(a["alias_video_frame_indices"]) for a in anchors)
    extraction_status = ("PASS_POSTHOC_EXTRACTION" if unknown == 0 and alias_count == 0 and
                         all(a["best_score"] <= FREEZE["anchor_max_score"] for a in anchors) else
                         "HOLD_TIMELINE_UNRESOLVED")
    result = {
        "schema": "astra-video-health-timing-a01-v1", "execution_id": FREEZE["execution_id"],
        "status": extraction_status, "base_commit": FREEZE["base_commit"],
        "freeze_sha256": sha((PACKAGE / "FREEZE.json").read_bytes()),
        "candidate_sha256": sha(Path(__file__).read_bytes()),
        "auditor_sha256": sha((PACKAGE / "audit.py").read_bytes()),
        "inputs": {field: FREEZE[field] for field in input_fields + ("wad_sha256",)},
        "ffmpeg_version": ffmpeg_version,
        "runtime": {**runtime, "platform": sys.platform, "game_or_gui_launched": False,
                    "model_calls": 0, "os_input_emitted": False},
        "video": {"frame_count": decoded_count, "fps": FREEZE["video_fps"],
                  "dimensions": FREEZE["video_size"],
                  "playback_rate_overlay": FREEZE["playback_rate_overlay"],
                  "decoder_stderr_sha256": decoder_stderr_sha256},
        "model_call": {"decision_index": FREEZE["model_decision_index"],
                       "start_ns": FREEZE["model_start_ns"], "end_ns": FREEZE["model_end_ns"],
                       "controller_elapsed_ns": FREEZE["model_end_ns"] - FREEZE["model_start_ns"],
                       "report_model_ns": FREEZE["reported_model_ns"],
                       "estimated_start_video_seconds": model_start_video,
                       "estimated_end_video_seconds": model_end_video,
                       "fit_uncertainty_seconds_only": fit_uncertainty,
                       "unmodeled_media_sync_uncertainty": "unknown",
                       "estimated_start_overlay_live_seconds": model_start_video * FREEZE["playback_rate_overlay"],
                       "estimated_end_overlay_live_seconds": model_end_video * FREEZE["playback_rate_overlay"],
                       "max_anchor_fit_residual_seconds": max(abs(v) for v in residual_seconds)},
        "clock_anchors": anchors, "capture_to_video_slope_ns_per_video_second": slope,
        "capture_to_video_intercept_ns": intercept,
        "capture_to_video_residual_seconds": residual_seconds,
        "health_reader": {"method": "WAD foreground templates with frozen per-channel tolerance",
                          "tolerance": FREEZE["channel_tolerance"],
                          "minimum_score": FREEZE["minimum_score"],
                          "minimum_margin": FREEZE["minimum_margin"],
                          "blank_score_below": FREEZE["blank_score_below"], "unknown_count": unknown},
        "transitions": transitions, "guard_floor_crossings_sensitivity_only": crossings,
        "historical_authored_guard": "none identified; sweep does not represent controller behavior",
        "rows": rows, "scope": FREEZE["scope"],
    }
    result_path = PACKAGE / "results" / "candidate.json"
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"execution_id": result["execution_id"], "status": result["status"],
                      "rows": len(rows), "unknown": unknown,
                      "anchors": [a["best_video_frame_indices"] for a in anchors],
                      "transitions": transitions, "model_end_video_seconds": model_end_video,
                      "fit_uncertainty_seconds_only": fit_uncertainty}, sort_keys=True))
    return 0 if result["status"] == "PASS_POSTHOC_EXTRACTION" else 1


if __name__ == "__main__":
    raise SystemExit(main())
