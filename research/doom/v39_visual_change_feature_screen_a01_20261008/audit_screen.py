from __future__ import annotations
import copy
import hashlib
import json
import math
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent
FRAMES = (166, 180, 190, 200, 210, 218)
HASHES = {
    166: "8c5e9c02dbc988693ec2126e92d9a2867d0f77ca9223e69356bcc6132b4b99d3",
    180: "7200e195e5c5a6bb1a859f4b3a73b6f6fdc6f5ff0baa1af0a5ef64e8c48de7a6",
    190: "e0942ccc712d7f862849120c0d4a13373c7e8d2866f3797bc5acfcebc6ec7d48",
    200: "0e6b6570944c3e0c60ca3eff5e84bc9371187cd8cea6a7d237e66cc06645483c",
    210: "33751e024d00058ce6cfa6404fad5804af96072e835f0818b18b01f5c4706831",
    218: "c711f3c36ff56778378a0f82275474615aac9879c2f61ce0d8d4ae8270e5a448",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def independently_recount(path: Path) -> tuple[int, int, list[tuple[int, int, int]]]:
    with Image.open(path) as opened:
        rgb = opened.convert("RGB")
        if rgb.size != (1280, 800):
            raise ValueError("dimension mismatch")
        view = rgb.crop((322, 181, 960, 583))
        scene = view.crop((0, 0, 638, 322))
        pixels = list(scene.getdata())
    # Integer-ratio form independently implements the frozen strict thresholds.
    warm = sum(20*r > 23*g and 10*g > 11*b and r >= 110 for r, g, b in pixels)
    red = sum(10*r > 14*g and 10*r > 13*b and r >= 120 for r, g, b in pixels)
    return warm, red, pixels


def validate(candidate: dict) -> bool:
    try:
        if candidate["schema"] != "issue59-visual-change-feature-screen-a01-v1":
            return False
        frames = candidate["frames"]
        if sorted(int(k) for k in frames) != list(FRAMES):
            return False
        counts = {}
        pixels = {}
        for seq in FRAMES:
            path = ROOT / "inputs" / f"{seq}.png"
            if digest(path) != HASHES[seq] or frames[str(seq)]["png_sha256"] != HASHES[seq]:
                return False
            warm, red, image_pixels = independently_recount(path)
            row = frames[str(seq)]
            if row["dimensions"] != [1280, 800] or row["warm_pixel_count"] != warm or row["red_pixel_count"] != red:
                return False
            area = 638 * 322
            if not math.isclose(row["warm_pixel_fraction"], warm / area, rel_tol=0, abs_tol=1e-15):
                return False
            if not math.isclose(row["red_pixel_fraction"], red / area, rel_tol=0, abs_tol=1e-15):
                return False
            counts[seq] = (warm, red)
            pixels[seq] = image_pixels
        expected_transitions = candidate["transitions"]
        if len(expected_transitions) != len(FRAMES) - 1:
            return False
        for i, (left_seq, right_seq) in enumerate(zip(FRAMES, FRAMES[1:])):
            left, right = pixels[left_seq], pixels[right_seq]
            mae_sum = 0
            changed = 0
            for p, q in zip(left, right):
                d = (abs(p[0]-q[0]), abs(p[1]-q[1]), abs(p[2]-q[2]))
                mae_sum += sum(d)
                changed += max(d) > 40
            row = expected_transitions[i]
            if row["from_sequence"] != left_seq or row["to_sequence"] != right_seq:
                return False
            if not math.isclose(row["normalized_rgb_mae"], mae_sum/(len(left)*3*255), rel_tol=0, abs_tol=1e-15):
                return False
            if not math.isclose(row["pixel_fraction_max_channel_delta_gt_40"], changed/len(left), rel_tol=0, abs_tol=1e-15):
                return False
        delta = counts[180][0]/(638*322) - counts[166][0]/(638*322)
        if not math.isclose(candidate["decision"]["warm_delta_166_to_180"], delta, rel_tol=0, abs_tol=1e-15):
            return False
        if candidate["decision"]["warm_candidate_threshold_met"] != (delta >= 0.005):
            return False
        red_rows = [seq for seq in FRAMES if counts[seq][1]/(638*322) - counts[166][1]/(638*322) >= 0.005]
        if candidate["decision"]["red_effect_positive_sequences_vs_166"] != red_rows:
            return False
        if candidate["decision"]["detector_validated"] is not False:
            return False
        return True
    except (KeyError, TypeError, ValueError, IndexError):
        return False


result = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))
checks = {
    "result_recomputed_from_six_hash_verified_pngs": validate(result),
    "mutation_corrupt_warm_count_detected": not validate({**result, "frames": {**result["frames"], "180": {**result["frames"]["180"], "warm_pixel_count": result["frames"]["180"]["warm_pixel_count"] + 1}}}),
    "mutation_corrupt_input_hash_detected": not validate({**result, "frames": {**result["frames"], "166": {**result["frames"]["166"], "png_sha256": "0" * 64}}}),
    "single_negative_frame_scope_retained": sum("No enemy" in row["single_reviewer_annotation"] for row in result["frames"].values()) == 1,
    "runtime_guard_not_claimed": result["decision"]["detector_validated"] is False,
}
audit = {
    "schema": "issue59-visual-change-feature-screen-a01-audit-v1",
    "status": "PASS_INDEPENDENT_RECOUNT" if all(checks.values()) else "FAIL_INDEPENDENT_RECOUNT",
    "checks": checks,
    "auditor_method": "separate integer-ratio threshold implementation and pixelwise transition recount using Pillow",
    "scope": "offline six-frame feature arithmetic and file integrity only; not label validation or detector efficacy",
}
(ROOT / "AUDIT.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
print(json.dumps(audit, indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
