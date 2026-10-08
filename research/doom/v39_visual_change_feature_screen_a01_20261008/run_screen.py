from __future__ import annotations
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent
INPUTS = ROOT / "inputs"
FRAMES = (166, 180, 190, 200, 210, 218)
EXPECTED_SHA256 = {
    166: "8c5e9c02dbc988693ec2126e92d9a2867d0f77ca9223e69356bcc6132b4b99d3",
    180: "7200e195e5c5a6bb1a859f4b3a73b6f6fdc6f5ff0baa1af0a5ef64e8c48de7a6",
    190: "e0942ccc712d7f862849120c0d4a13373c7e8d2866f3797bc5acfcebc6ec7d48",
    200: "0e6b6570944c3e0c60ca3eff5e84bc9371187cd8cea6a7d237e66cc06645483c",
    210: "33751e024d00058ce6cfa6404fad5804af96072e835f0818b18b01f5c4706831",
    218: "c711f3c36ff56778378a0f82275474615aac9879c2f61ce0d8d4ae8270e5a448",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    timeline = json.loads((INPUTS / "VISUAL_THREAT_TIMELINE.json").read_text(encoding="utf-8"))
    labels = timeline["single_reviewer_pixel_annotations"]
    scenes = {}
    records = {}
    for sequence in FRAMES:
        path = INPUTS / f"{sequence}.png"
        actual_hash = sha256(path)
        if actual_hash != EXPECTED_SHA256[sequence]:
            raise ValueError(f"input hash mismatch for {path.name}: {actual_hash}")
        with Image.open(path) as image:
            rgb = image.convert("RGB")
            if rgb.size != (1280, 800):
                raise ValueError(f"unexpected image dimensions for {path.name}: {rgb.size}")
            # Fixed game viewport, excluding titlebar/black margins; upper 80% excludes HUD.
            viewport = rgb.crop((322, 181, 960, 583))
            scene = viewport.crop((0, 0, 638, 322))
            pixels = list(scene.getdata())
        warm = sum(1 for r, g, b in pixels if r >= 110 and r > 1.15 * g and g > 1.10 * b)
        red = sum(1 for r, g, b in pixels if r >= 120 and r > 1.40 * g and r > 1.30 * b)
        records[sequence] = {
            "png_sha256": actual_hash,
            "dimensions": list(rgb.size),
            "game_viewport_xyxy": [322, 181, 960, 583],
            "scene_height_pixels": 322,
            "single_reviewer_annotation": labels[str(sequence)],
            "warm_pixel_count": warm,
            "warm_pixel_fraction": warm / len(pixels),
            "red_pixel_count": red,
            "red_pixel_fraction": red / len(pixels),
        }
        scenes[sequence] = pixels

    transitions = []
    width, height = 638, 322
    for previous, current in zip(FRAMES, FRAMES[1:]):
        left, right = scenes[previous], scenes[current]
        delta_total = 0
        changed = 0
        for a, b in zip(left, right):
            channel_delta = [abs(a[i] - b[i]) for i in range(3)]
            delta_total += sum(channel_delta)
            changed += max(channel_delta) > 40
        transitions.append({
            "from_sequence": previous,
            "to_sequence": current,
            "normalized_rgb_mae": delta_total / (len(left) * 3 * 255),
            "pixel_fraction_max_channel_delta_gt_40": changed / len(left),
        })

    baseline = records[166]["warm_pixel_fraction"]
    warm_delta_180 = records[180]["warm_pixel_fraction"] - baseline
    warm_positive = warm_delta_180 >= 0.005
    red_positive_frames = [
        sequence for sequence in FRAMES
        if records[sequence]["red_pixel_fraction"] - records[166]["red_pixel_fraction"] >= 0.005
    ]
    output = {
        "schema": "issue59-visual-change-feature-screen-a01-v1",
        "disposition": "EXPLORATORY_FEATURE_SCREEN_ONLY",
        "input_provenance": {
            "prior_timeline_schema": timeline["schema"],
            "prior_episode": timeline["episode"]["allocation_id"],
            "frame_sequences": list(FRAMES),
            "labels_source": "single_reviewer_pixel_annotations in copied prior timeline JSON",
        },
        "fixed_feature_definitions": {
            "scene_crop": {"viewport_xyxy": [322, 181, 960, 583], "upper_scene_height": 322},
            "warm": "R >= 110 and R > 1.15*G and G > 1.10*B",
            "red": "R >= 120 and R > 1.40*G and R > 1.30*B",
            "adjacent_frame_change": "normalized RGB MAE and fraction with max-channel absolute delta > 40",
            "candidate_threshold": 0.005,
        },
        "frames": records,
        "transitions": transitions,
        "decision": {
            "warm_delta_166_to_180": warm_delta_180,
            "warm_candidate_threshold_met": warm_positive,
            "red_effect_positive_sequences_vs_166": red_positive_frames,
            "false_alarm_rate_estimable": False,
            "detector_validated": False,
        },
        "limits": [
            "Six selected frames from one episode; one reviewer supplied all visual labels.",
            "Only frame 166 is annotated enemy-absent; there are no balanced harmless-motion controls.",
            "No threshold fitting, temporal sampling analysis, live capture timing, false-interrupt estimate, or task effect.",
            "Pixel features can respond to camera motion, scenery, animation, lighting, and damage effects.",
            "This record does not authorize or implement a runtime guard or live allocation.",
        ],
    }
    (ROOT / "RESULT.json").write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(output["decision"], indent=2))
    print(json.dumps(transitions, indent=2))


if __name__ == "__main__":
    main()
