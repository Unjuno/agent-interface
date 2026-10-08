#!/usr/bin/env python3
"""One-shot byte-accounting candidate; no GUI, model, network, or action APIs."""
from __future__ import annotations

import base64
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, __version__ as PILLOW_VERSION

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ALLOCATION = "LABEL-CONTROL-AMBIGUITY-1998-T0-A04-20261009"
BASE = "4758a95cd4a0aaa78e9cdc9d774f298d4ccf0e36"
sys.path.insert(0, str(REPO / "research" / "observation_tiles"))
from image_artifact import ImageArtifactSink  # noqa: E402


@dataclass(frozen=True)
class Frame:
    width: int
    height: int
    mode: str
    pixels: bytes


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def resolve_source(path: str) -> Path:
    return REPO / path


def verify_freeze() -> tuple[dict, dict]:
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    if freeze.get("allocation") != ALLOCATION or freeze.get("base_commit") != BASE:
        raise SystemExit("STOP_FREEZE_ID_OR_BASE")
    for key, expected in freeze["source_sha256"].items():
        if key.startswith("repo/"):
            path = REPO / key[len("repo/"):]
        elif key.startswith("package/"):
            path = HERE / key[len("package/"):]
        else:
            raise SystemExit("STOP_UNKNOWN_FROZEN_PATH:" + key)
        if sha(path.read_bytes()) != expected:
            raise SystemExit("STOP_SOURCE_HASH:" + key)
    design = json.loads((HERE / "design.json").read_text(encoding="utf-8"))
    return freeze, design


def pixel_digest(width: int, height: int, mode: str, pixels: bytes) -> str:
    return sha(f"{width},{height},{mode}:".encode("ascii") + pixels)


def bounds_for(width: int, height: int, crop_width: int, crop_height: int, placement: str) -> list[int]:
    offsets = {
        "center": ((width - crop_width) // 2, (height - crop_height) // 2),
        "top_left": (0, 0),
        "top_right": (width - crop_width, 0),
        "bottom_left": (0, height - crop_height),
        "bottom_right": (width - crop_width, height - crop_height),
    }
    x0, y0 = offsets[placement]
    return [x0, y0, x0 + crop_width, y0 + crop_height]


def expected_cases(frame: dict, width: int, height: int, design: dict) -> list[dict]:
    cases = []
    for area_id, (crop_width, crop_height) in design["area_sizes_pixels"].items():
        if crop_width >= width or crop_height >= height or crop_width <= 0 or crop_height <= 0:
            raise ValueError("invalid frozen ROI size")
        for placement in design["placements"]:
            bounds = bounds_for(width, height, crop_width, crop_height, placement)
            cases.append({
                "case_id": f"{frame['frame_id']}__{area_id}__{placement}",
                "frame_id": frame["frame_id"],
                "request": {"frame_id": frame["frame_id"], "epoch": frame["epoch"],
                            "region_id": f"{area_id}-{placement}",
                            "candidate_region_ids": [f"{area_id}-{placement}"],
                            "reason": "uncertain", "bounds": bounds},
                "expected_crop_width": crop_width,
                "expected_crop_height": crop_height,
            })
    cases.append({
        "case_id": f"{frame['frame_id']}__full_bounds_control",
        "frame_id": frame["frame_id"],
        "request": {"frame_id": frame["frame_id"], "epoch": frame["epoch"],
                    "region_id": "full-bounds-control", "candidate_region_ids": ["full-bounds-control"],
                    "reason": "uncertain", "bounds": [0, 0, width, height]},
        "expected_crop_width": width,
        "expected_crop_height": height,
    })
    return cases


def encode_artifact(pixels: bytes, width: int, height: int, mode: str, target: Path) -> bytes:
    target.parent.mkdir(parents=True, exist_ok=True)
    sink = ImageArtifactSink(target.parent, compress_level=6, reuse=False)
    result = sink.publish(Frame(width, height, mode, pixels))
    actual = Path(result["image"])
    actual.replace(target)
    return target.read_bytes()


def payload(frame: dict, width: int, height: int, png: bytes, *, kind: str,
            request: dict | None = None) -> dict:
    item = {"schema": "focused-observation-png-v1", "kind": kind,
            "media_type": "image/png", "frame_id": frame["frame_id"],
            "epoch": frame["epoch"], "width": width, "height": height,
            "encoding": "RGB8", "png_b64": base64.b64encode(png).decode("ascii")}
    if request is not None:
        item.update({"region_id": request["region_id"], "bounds": request["bounds"],
                     "reason": request["reason"]})
    return item


def run() -> dict:
    freeze, design = verify_freeze()
    if PILLOW_VERSION != freeze["pillow_version"]:
        raise SystemExit("STOP_PILLOW_VERSION_MISMATCH")
    artifact_root = HERE / "results" / "artifacts"
    artifact_root.mkdir(parents=True, exist_ok=False)
    frame_artifacts = []
    all_rows = []
    for frame in design["frames"]:
        source_path = resolve_source(frame["source_png_path"])
        with Image.open(source_path) as source_image:
            if source_image.mode != "RGB":
                raise SystemExit("STOP_SOURCE_MODE:" + frame["frame_id"])
            source_image.load()
            width, height = source_image.size
            pixels = source_image.tobytes()
        if (width, height) != (1280, 800):
            raise SystemExit("STOP_SOURCE_DIMENSIONS:" + frame["frame_id"])
        if pixel_digest(width, height, "RGB", pixels) != frame["source_pixel_sha256"]:
            raise SystemExit("STOP_SOURCE_PIXEL_IDENTITY:" + frame["frame_id"])
        full_path = f"results/artifacts/full/{frame['frame_id']}/frame.png"
        full_bytes = encode_artifact(pixels, width, height, "RGB", HERE / full_path)
        full_payload = payload(frame, width, height, full_bytes, kind="FULL_FRAME")
        frame_artifacts.append({
            "frame_id": frame["frame_id"], "source_pixel_sha256": frame["source_pixel_sha256"],
            "full_png_path": full_path, "full_png_sha256": sha(full_bytes),
            "full_png_bytes": len(full_bytes), "full_payload_bytes": len(canonical(full_payload)),
        })
        source_image = Image.frombytes("RGB", (width, height), pixels)
        for case in expected_cases(frame, width, height, design):
            x0, y0, x1, y1 = case["request"]["bounds"]
            focused_image = source_image.crop((x0, y0, x1, y1))
            crop_pixels = focused_image.tobytes()
            crop_path = f"results/artifacts/crops/{case['case_id']}/crop.png"
            crop_bytes = encode_artifact(crop_pixels, x1 - x0, y1 - y0, "RGB", HERE / crop_path)
            focus_payload = payload(frame, x1 - x0, y1 - y0, crop_bytes,
                                    kind="FOCUSED_REGION", request=case["request"])
            focus_payload_bytes = len(canonical(focus_payload))
            full_payload_bytes = len(canonical(full_payload))
            focused_selected = focus_payload_bytes < full_payload_bytes
            selected_bytes = focus_payload_bytes if focused_selected else full_payload_bytes
            all_rows.append({
                "case_id": case["case_id"], "frame_id": frame["frame_id"],
                "request": case["request"], "crop_width": x1 - x0, "crop_height": y1 - y0,
                "focus_png_path": crop_path, "focus_png_sha256": sha(crop_bytes),
                "focus_png_bytes": len(crop_bytes), "focus_payload_bytes": focus_payload_bytes,
                "full_payload_bytes": full_payload_bytes,
                "selected_kind": "FOCUSED_REGION" if focused_selected else "FULL_FRAME",
                "selected_payload_bytes": selected_bytes,
                "bytes_saved_vs_full": full_payload_bytes - selected_bytes,
                "decision": "FOCUSED_REGION_SELECTED" if focused_selected else "FULL_FRAME_NO_SIZE_GAIN",
            })
        source_image.close()
    return {
        "schema": "1998-a04-pillow-png-payload-raw-v1", "allocation": ALLOCATION,
        "base_commit": BASE, "freeze_sha256": sha((HERE / "FREEZE.json").read_bytes()),
        "encoder_source_sha256": freeze["source_sha256"]["repo/research/observation_tiles/image_artifact.py"],
        "pillow_version": PILLOW_VERSION, "compress_level": 6,
        "frame_count": len(frame_artifacts), "case_count": len(all_rows),
        "frames": frame_artifacts, "rows": all_rows,
    }


def main() -> None:
    print(json.dumps(run(), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
