#!/usr/bin/env python3
"""One-shot deterministic PNG crop payload comparison; no GUI or network."""
import base64
import binascii
import hashlib
import json
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ALLOCATION = "LABEL-CONTROL-AMBIGUITY-1998-T0-A03-20261009"
BASE = "4758a95cd4a0aaa78e9cdc9d774f298d4ccf0e36"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def chunk(kind: bytes, payload: bytes) -> bytes:
    body = kind + payload
    return struct.pack(">I", len(payload)) + body + struct.pack(">I", binascii.crc32(body) & 0xFFFFFFFF)


def encode_png(width: int, height: int, rgb: bytes) -> bytes:
    if len(rgb) != width * height * 3:
        raise ValueError("RGB8 length mismatch")
    rows = b"".join(b"\x00" + rgb[y * width * 3:(y + 1) * width * 3] for y in range(height))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return PNG_SIGNATURE + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(rows, 6)) + chunk(b"IEND", b"")


def crop_rgb(source: bytes, width: int, bounds: list[int]) -> tuple[int, int, bytes]:
    x0, y0, x1, y1 = bounds
    out_width = x1 - x0
    rows = [source[(y * width + x0) * 3:(y * width + x1) * 3] for y in range(y0, y1)]
    return out_width, y1 - y0, b"".join(rows)


def load_inputs() -> tuple[dict, dict[str, bytes]]:
    freeze = json.loads((ROOT / "FREEZE.json").read_text())
    if freeze["allocation"] != ALLOCATION or freeze["base_commit"] != BASE:
        raise SystemExit("STOP_FREEZE_ID_OR_BASE")
    for name, expected in freeze["source_sha256"].items():
        if sha(ROOT / name) != expected:
            raise SystemExit("STOP_SOURCE_HASH:" + name)
    design = json.loads((ROOT / "design.json").read_text())
    sources = {f["frame_id"]: (ROOT / f["source"]).read_bytes() for f in design["frames"]}
    return design, sources


def refusal(request: dict, frame: dict, width: int, height: int) -> str | None:
    if request["reason"] != "uncertain":
        return "REASON_NOT_UNCERTAIN"
    if request["frame_id"] != frame["frame_id"]:
        return "STALE_FRAME_IDENTITY"
    if request["epoch"] != frame["epoch"]:
        return "STALE_EPOCH"
    if request["focus_state"] != "active":
        return "FOCUS_NOT_ACTIVE"
    if request["candidate_region_ids"] != [request["region_id"]]:
        return "AMBIGUOUS_REGION"
    bounds = request["bounds"]
    if (len(bounds) != 4 or any(type(v) is not int for v in bounds)
            or not (0 <= bounds[0] < bounds[2] <= width and 0 <= bounds[1] < bounds[3] <= height)):
        return "REGION_OUT_OF_BOUNDS"
    return None


def make_full(frame: dict, width: int, height: int, png: bytes) -> dict:
    return {"schema": "focused-observation-png-v1", "kind": "FULL_FRAME",
            "media_type": "image/png", "frame_id": frame["frame_id"],
            "epoch": frame["epoch"], "width": width, "height": height,
            "encoding": "RGB8", "png_b64": base64.b64encode(png).decode("ascii")}


def make_focus(frame: dict, request: dict, width: int, height: int, png: bytes) -> dict:
    return {"schema": "focused-observation-png-v1", "kind": "FOCUSED_REGION",
            "media_type": "image/png", "frame_id": frame["frame_id"],
            "epoch": frame["epoch"], "width": width, "height": height,
            "encoding": "RGB8", "region_id": request["region_id"],
            "bounds": request["bounds"], "reason": request["reason"],
            "png_b64": base64.b64encode(png).decode("ascii")}


def run(design: dict, sources: dict[str, bytes]) -> dict:
    width, height = design["width"], design["height"]
    frames = {f["frame_id"]: f for f in design["frames"]}
    rows = []
    for frame_desc in design["frames"]:
        source = sources[frame_desc["frame_id"]]
        full_png = encode_png(width, height, source)
        full_payload = make_full(frame_desc, width, height, full_png)
        full_bytes = len(canonical(full_payload))
        for roi in design["valid_rois"]:
            request = {"reason": "uncertain", "frame_id": frame_desc["frame_id"],
                       "epoch": frame_desc["epoch"], "focus_state": "active",
                       "region_id": roi["roi_id"], "candidate_region_ids": [roi["roi_id"]],
                       "bounds": roi["bounds"]}
            x0, y0, x1, y1 = request["bounds"]
            crop_w, crop_h, crop = crop_rgb(source, width, request["bounds"])
            focus_png = encode_png(crop_w, crop_h, crop)
            focus_payload = make_focus(frame_desc, request, crop_w, crop_h, focus_png)
            focus_bytes = len(canonical(focus_payload))
            selected_focus = focus_bytes < full_bytes
            selected = focus_payload if selected_focus else full_payload
            rows.append({"case_id": frame_desc["pattern"] + ":" + roi["roi_id"],
                         "request": request, "full_frame_payload": full_payload,
                         "full_frame_bytes": full_bytes, "focused_payload": focus_payload,
                         "focused_bytes": focus_bytes,
                         "selected_kind": "FOCUSED_REGION" if selected_focus else "FULL_FRAME",
                         "selected_payload": selected, "selected_bytes": len(canonical(selected)),
                         "bytes_saved_vs_full": full_bytes - len(canonical(selected)),
                         "decision": "FOCUSED_REGION_SELECTED" if selected_focus else "FULL_FRAME_NO_SIZE_GAIN"})
    frame_desc = frames["frame-flat_ui"]
    full_png = encode_png(width, height, sources[frame_desc["frame_id"]])
    full_payload = make_full(frame_desc, width, height, full_png)
    full_bytes = len(canonical(full_payload))
    for invalid in design["invalid_requests"]:
        request = dict(invalid)
        case_id = request.pop("case_id")
        rows.append({"case_id": case_id, "request": request,
                     "full_frame_payload": full_payload, "full_frame_bytes": full_bytes,
                     "focused_payload": None, "focused_bytes": None,
                     "selected_kind": "FULL_FRAME", "selected_payload": full_payload,
                     "selected_bytes": full_bytes, "bytes_saved_vs_full": 0,
                     "decision": "ABSTAIN_" + (refusal(request, frame_desc, width, height) or "UNEXPECTED_VALID")})
    return {"schema": "1998-a03-png-payload-raw-v1", "allocation": ALLOCATION,
            "base_commit": BASE, "case_count": len(rows), "rows": rows}


def main() -> None:
    design, sources = load_inputs()
    print(json.dumps(run(design, sources), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
