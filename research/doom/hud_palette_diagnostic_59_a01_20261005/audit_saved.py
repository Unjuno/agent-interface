"""Independent read-only reconstruction of the retained palette scores."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import struct

import numpy as np
from PIL import Image, __version__ as pillow_version


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ANCHORS = {"health": (102, 411), "ammo": (10, 411)}
WIDTH, HEIGHT, SLOTS = 26, 38, 3
MIN_SCORE, MIN_MARGIN = 0.80, 0.05


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def parse_wad(data):
    if len(data) < 12:
        raise ValueError("short WAD header")
    ident, count, directory = struct.unpack_from("<4sII", data, 0)
    if ident not in (b"IWAD", b"PWAD") or directory + count * 16 > len(data):
        raise ValueError("invalid WAD header or directory")
    lumps = {}
    for index in range(count):
        offset, size, raw_name = struct.unpack_from("<II8s", data, directory + index * 16)
        if offset + size > len(data):
            raise ValueError("lump outside WAD")
        lumps[raw_name.rstrip(b"\0").decode("ascii", "strict")] = data[offset:offset + size]
    return lumps


def render_patch(patch, palette):
    """Decode one Doom column patch without calling the production reader."""
    if len(patch) < 8:
        raise ValueError("short patch header")
    width, height, _left, _top = struct.unpack_from("<hhhh", patch, 0)
    if width < 1 or height < 1 or 8 + width * 4 > len(patch):
        raise ValueError("invalid patch geometry")
    indices = np.zeros((height, width), dtype=np.uint8)
    alpha = np.zeros((height, width), dtype=np.uint8)
    for x in range(width):
        cursor = struct.unpack_from("<I", patch, 8 + 4 * x)[0]
        posts = 0
        while True:
            if cursor >= len(patch):
                raise ValueError("unterminated patch column")
            top = patch[cursor]
            if top == 255:
                break
            if cursor + 4 > len(patch):
                raise ValueError("truncated patch post")
            length = patch[cursor + 1]
            begin, end = cursor + 3, cursor + 3 + length
            if end + 1 > len(patch) or top + length > height:
                raise ValueError("invalid patch post bounds")
            indices[top:top + length, x] = np.frombuffer(patch[begin:end], dtype=np.uint8)
            alpha[top:top + length, x] = 255
            cursor = end + 1
            posts += 1
            if posts > height:
                raise ValueError("excess patch posts")
    return np.dstack((palette[indices], alpha))


def templates_for(lumps, palette):
    templates = []
    for digit in range(10):
        rgba = Image.fromarray(render_patch(lumps[f"STTNUM{digit}"], palette))
        resized = np.asarray(rgba.resize((WIDTH, HEIGHT), Image.Resampling.NEAREST))
        templates.append((resized[:, :, :3], resized[:, :, 3] > 0))
    return templates


def score_frame(frame, observation, signal, templates, wad_hash):
    geometry = observation["pointer_binding"]["geometry"]
    left = geometry[0] + ANCHORS[signal][0]
    top = geometry[1] + ANCHORS[signal][1]
    if left < 0 or top < 0 or left + WIDTH * SLOTS > frame.width or top + HEIGHT > frame.height:
        raise ValueError("saved number ROI outside frame")
    pixels = np.asarray(frame.crop((left, top, left + WIDTH * SLOTS, top + HEIGHT)))
    digits, slot_rows, score_vectors = [], [], []
    for slot in range(SLOTS):
        crop = pixels[:, slot * WIDTH:(slot + 1) * WIDTH]
        scores = []
        for image, mask in templates:
            scores.append(float(np.all(crop == image, axis=2)[mask].mean()))
        order = sorted(range(10), key=scores.__getitem__, reverse=True)
        best, second = order[:2]
        digit = None if scores[best] < MIN_SCORE else best
        row = {"slot": slot, "digit": digit, "best_digit": best,
               "best_score": scores[best], "second_score": scores[second]}
        digits.append(digit)
        slot_rows.append(row)
        score_vectors.append(scores)
        if digit is not None and scores[best] - scores[second] < MIN_MARGIN:
            return ({"status": "unknown", "reason": "ambiguous_digit", "value": None,
                     "detail": {"slot": slot, "scores": scores}}, slot_rows, score_vectors)
    first = next((idx for idx, digit in enumerate(digits) if digit is not None), None)
    if (first is None or any(digit is None for digit in digits[first:]) or
            any(digit is not None for digit in digits[:first])):
        return ({"status": "unknown", "reason": "invalid_right_aligned_number",
                 "value": None, "detail": {"slots": slot_rows}}, slot_rows, score_vectors)
    value = int("".join(str(digit) for digit in digits[first:]))
    return ({"status": "observed", "reason": None, "value": value,
             "slots": slot_rows, "wad_sha256": wad_hash}, slot_rows, score_vectors)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wad", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=HERE / "audit-result.json")
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("audit output already exists; preserve first result")

    started = datetime.now(timezone.utc).isoformat()
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    freeze_bytes = (HERE / "FREEZE.json").read_bytes()
    candidate = json.loads((HERE / "run-01" / "result.json").read_text())
    checks = {}
    checks["candidate_freeze_join"] = candidate.get("freeze_sha256") == sha256(freeze_bytes)
    for relative, expected in freeze["repo_sha256"].items():
        checks["frozen_sha256:" + relative] = sha256((ROOT / relative).read_bytes()) == expected
    wad_bytes = args.wad.read_bytes()
    checks["wad_sha256"] = sha256(wad_bytes) == freeze["wad_sha256"]
    if not all(checks.values()):
        raise SystemExit("frozen input hash mismatch; refusing audit")
    lumps = parse_wad(wad_bytes)
    playpal_bytes = lumps.get("PLAYPAL", b"")
    checks["playpal_digest"] = sha256(playpal_bytes) == candidate["playpal_sha256"]
    checks["playpal_complete"] = bool(playpal_bytes) and len(playpal_bytes) % 768 == 0
    if not all(checks.values()):
        raise SystemExit("PLAYPAL custody/shape mismatch; refusing audit")
    palettes = np.frombuffer(playpal_bytes, dtype=np.uint8).reshape(-1, 256, 3)
    checks["palette_count"] = len(palettes) == candidate["palette_count"]

    archive = ROOT / freeze["archive"]
    runtime = archive / "guarded/run/episode/runtime"
    event_path = runtime / "events.jsonl"
    observations = [json.loads(line) for line in event_path.read_text().splitlines()]
    by_sequence = {}
    for sequence in freeze["sequences"]:
        rows = [row for row in observations if row.get("event") == "observation"
                and row.get("sequence") == sequence]
        checks[f"single_observation:{sequence}"] = len(rows) == 1
        if len(rows) != 1:
            raise SystemExit(f"observation identity ambiguous at sequence {sequence}")
        by_sequence[sequence] = rows[0]
    checks["event_log_hash"] = sha256(event_path.read_bytes()) == freeze["repo_sha256"][
        "research/doom/v16_comparison_unknown_59_4d74_20261004/guarded/run/episode/runtime/events.jsonl"]

    audit_rows = []
    raw_rows = {(row["sequence"], row["signal"]): row for row in candidate["rows"]}
    expected_row_count = len(freeze["sequences"]) * len(ANCHORS)
    checks["candidate_rows_complete"] = (
        len(candidate["rows"]) == expected_row_count and len(raw_rows) == expected_row_count)
    if not checks["candidate_rows_complete"] or not checks["candidate_freeze_join"]:
        raise SystemExit("candidate row identity/freeze join failed")
    original = json.loads((archive / "saved-hud-probe-01" / "result.json").read_text())
    original_baselines = {(row["sequence"], row["signal"]): row["file"] for row in original}
    for sequence in freeze["sequences"]:
        observation = by_sequence[sequence]
        image_path = runtime / f"{sequence:03}.png"
        with Image.open(image_path) as opened:
            frame = opened.convert("RGB")
        frame_hash = sha256(frame.tobytes())
        checks[f"rgb_join:{sequence}"] = frame_hash == observation["frame_rgb_sha256"]
        for signal in ("health", "ammo"):
            raw = raw_rows[(sequence, signal)]
            checks[f"palette0_baseline_match:{sequence}:{signal}"] = (
                raw["palette_variants"][0]["outcome"] == original_baselines[(sequence, signal)])
            if not checks[f"palette0_baseline_match:{sequence}:{signal}"]:
                raise SystemExit("palette-0 projection differs from retained baseline")
            checks[f"candidate_frame_join:{sequence}:{signal}"] = (
                raw["frame_rgb_sha256"] == frame_hash and
                raw["baseline"]["sequence"] == sequence and
                raw["baseline"]["capture_ns"] == observation["capture_ns"] and
                raw["baseline"]["binding"] == observation["pointer_binding"])
            if not checks[f"rgb_join:{sequence}"] or not checks[f"candidate_frame_join:{sequence}:{signal}"]:
                raise SystemExit("candidate/frame/source observation join failed")
            variants = raw["palette_variants"]
            checks[f"all_palettes_retained:{sequence}:{signal}"] = (
                len(variants) == len(palettes) and
                [variant["palette"] for variant in variants] == list(range(len(palettes))))
            for index, palette in enumerate(palettes):
                projected, slot_rows, score_vectors = score_frame(
                    frame, observation, signal, templates_for(lumps, palette), freeze["wad_sha256"])
                stored = variants[index]["outcome"]
                checks[f"outcome_match:{sequence}:{signal}:{index}"] = (
                    stored["status"] == projected["status"] and
                    stored.get("reason") == projected["reason"] and
                    stored.get("value") == projected["value"])
                stored_slots = (stored.get("slots") if projected["status"] == "observed"
                                else stored.get("detail", {}).get("slots"))
                if projected["reason"] == "ambiguous_digit":
                    stored_slots = []
                    stored_detail = stored.get("detail", {})
                    checks[f"ambiguous_detail_match:{sequence}:{signal}:{index}"] = (
                        stored_detail.get("slot") == projected["detail"]["slot"] and
                        stored_detail.get("scores") == projected["detail"]["scores"])
                else:
                    checks[f"slot_projection_match:{sequence}:{signal}:{index}"] = (
                        isinstance(stored_slots, list) and len(stored_slots) == len(slot_rows) and
                        all(all(stored_row.get(key) == expected_row.get(key)
                                for key in ("slot", "digit", "best_digit", "best_score", "second_score"))
                            for stored_row, expected_row in zip(stored_slots, slot_rows)))
                if not all(checks[key] for key in checks
                           if key.endswith(f":{sequence}:{signal}:{index}") or
                           key == f"slot_projection_match:{sequence}:{signal}:{index}"):
                    raise SystemExit("independent glyph score disagrees with retained candidate")
                audit_rows.append({"sequence": sequence, "signal": signal,
                                   "palette": index, "projection": projected,
                                   "foreground_score_vectors": score_vectors})

    if not all(checks.values()):
        raise SystemExit("one or more independent audit checks failed")
    accepted = {}
    for sequence in freeze["sequences"]:
        for signal in ("health", "ammo"):
            accepted[f"{sequence}:{signal}"] = [
                row["palette"] for row in audit_rows
                if row["sequence"] == sequence and row["signal"] == signal and
                row["projection"]["status"] == "observed"]
    report = {
        "schema": "saved-hud-palette-independent-audit-v1",
        "disposition": "PASS_RETAINED_RGB_AND_GLYPH_SCORE_RECONSTRUCTION",
        "checks": len(checks),
        "passed_checks": sum(bool(value) for value in checks.values()),
        "source_commit": freeze["source_commit"],
        "wad_sha256": freeze["wad_sha256"],
        "playpal_sha256": sha256(playpal_bytes),
        "palette_count": len(palettes),
        "sequences": freeze["sequences"],
        "rgb_frame_sha256": {str(seq): by_sequence[seq]["frame_rgb_sha256"]
                             for seq in freeze["sequences"]},
        "accepted_palettes_by_sequence_signal": accepted,
        "score_method": "independent Doom patch/WAD decoder; exact RGB per alpha-foreground pixel; 26x38 nearest resize; fixed ROI and 0.80/0.05 thresholds",
        "claim_boundary": "reproduces the frozen reader's outcomes and scores for two saved frames; does not establish selected renderer palette or independent HUD ground truth",
        "python": platform.python_version(),
        "pillow": pillow_version,
        "numpy": np.__version__,
        "started_at": started,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "checks_detail": checks,
        "independent_score_rows": audit_rows,
    }
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: report[key] for key in (
        "schema", "disposition", "checks", "accepted_palettes_by_sequence_signal",
        "claim_boundary")} , sort_keys=True))


if __name__ == "__main__":
    main()
