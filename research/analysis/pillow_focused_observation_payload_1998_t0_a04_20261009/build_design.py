#!/usr/bin/env python3
"""Build the fixed design from the already-retained baseline-screen-02 ledgers."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
INPUT_ROOT = Path("research/observation_gating/results/baseline-screen-02")
AREA_SIZES = {
    "a01_16": (320, 200),
    "a04_16": (640, 400),
    "a08_16": (800, 640),
    "a12_16": (1024, 750),
}
PLACEMENTS = ("center", "top_left", "top_right", "bottom_left", "bottom_right")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    frames = []
    ledgers = []
    for ledger in sorted((REPO / INPUT_ROOT).glob("*/observations.jsonl")):
        ledger_rel = ledger.relative_to(REPO).as_posix()
        ledger_bytes = ledger.read_bytes()
        ledgers.append({"path": ledger_rel, "sha256": sha(ledger_bytes)})
        app = ledger.parent.name.split("-1101-O0", 1)[0]
        seen = set()
        for line in ledger.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            pixel_sha = row["sha256"]
            if pixel_sha in seen:
                continue
            seen.add(pixel_sha)
            image_path = ledger.parent / "frames" / f"{pixel_sha}.png"
            image_bytes = image_path.read_bytes()
            frame_id = f"{app}-{pixel_sha[:12]}"
            frames.append({
                "frame_id": frame_id,
                "application": app,
                "epoch": row["sequence"],
                "first_action_id": row["action_id"],
                "ledger_path": ledger_rel,
                "ledger_sequence": row["sequence"],
                "source_pixel_sha256": pixel_sha,
                "source_png_path": image_path.relative_to(REPO).as_posix(),
                "source_png_sha256": sha(image_bytes),
            })
    if len(ledgers) != 4 or len(frames) != 21:
        raise SystemExit(f"fixture coverage mismatch: ledgers={len(ledgers)} frames={len(frames)}")
    design = {
        "allocation": "LABEL-CONTROL-AMBIGUITY-1998-T0-A04-20261009",
        "base_commit": "4758a95cd4a0aaa78e9cdc9d774f298d4ccf0e36",
        "question": "Pillow ImageArtifactSink PNG crop payload economics on retained GUI frames",
        "encoder_source": "research/observation_tiles/image_artifact.py",
        "encoder_compress_level": 6,
        "inputs": sorted(ledgers, key=lambda item: item["path"]),
        "frames": sorted(frames, key=lambda item: (item["application"], item["epoch"], item["frame_id"])),
        "area_sizes_pixels": AREA_SIZES,
        "placements": list(PLACEMENTS),
        "full_bounds_control_per_frame": True,
        "expected_crop_cases": len(frames) * len(AREA_SIZES) * len(PLACEMENTS),
        "expected_full_bounds_controls": len(frames),
        "expected_case_count": len(frames) * (len(AREA_SIZES) * len(PLACEMENTS) + 1),
        "roi_bounds_rule": "fixed integer crop sizes; center uses floor((dimension-size)/2); corners use zero/max offsets",
        "order": "frames sorted by application, epoch, frame_id; each frame has area key order then placement order, followed by full-bounds control",
    }
    (HERE / "design.json").write_text(json.dumps(design, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"frames": len(frames), "ledgers": len(ledgers), "cases": design["expected_case_count"]}, sort_keys=True))


if __name__ == "__main__":
    main()
