#!/usr/bin/env python3
"""Independent raw-only A10 auditor using Python standard library."""
import argparse
import copy
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path

PNG_SIG = b"\x89PNG\r\n\x1a\n"
IMAGE_ROOT = Path("research/observation_gating/results/baseline-screen-02/chromium-1101-O0/frames")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    return a if pa <= pb and pa <= pc else b if pb <= pc else c


def decode_png(data: bytes):
    if not data.startswith(PNG_SIG):
        raise ValueError("bad PNG signature")
    pos, width, height, bit_depth, color_type = 8, None, None, None, None
    compressed = []
    ended = False
    while pos < len(data):
        if pos + 12 > len(data):
            raise ValueError("truncated PNG chunk")
        n = struct.unpack_from(">I", data, pos)[0]
        pos += 4
        kind = data[pos:pos + 4]
        pos += 4
        if pos + n + 4 > len(data):
            raise ValueError("truncated PNG data")
        chunk = data[pos:pos + n]
        pos += n
        expected_crc = struct.unpack_from(">I", data, pos)[0]
        pos += 4
        if zlib.crc32(kind + chunk) & 0xFFFFFFFF != expected_crc:
            raise ValueError(f"bad PNG CRC in {kind!r}")
        if kind == b"IHDR":
            if n != 13:
                raise ValueError("bad IHDR length")
            width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(">IIBBBBB", chunk)
            if (bit_depth, color_type, compression, filtering, interlace) != (8, 2, 0, 0, 0):
                raise ValueError("only non-interlaced 8-bit RGB PNG is supported")
        elif kind == b"IDAT":
            compressed.append(chunk)
        elif kind == b"IEND":
            ended = True
            break
    if not ended or width is None or not compressed:
        raise ValueError("missing PNG structure")
    stride, bpp = width * 3, 3
    raw = zlib.decompress(b"".join(compressed))
    if len(raw) != height * (stride + 1):
        raise ValueError("wrong scanline length")
    pixels = bytearray(height * stride)
    cursor = 0
    for y in range(height):
        filt = raw[cursor]
        cursor += 1
        row = y * stride
        for x in range(stride):
            value = raw[cursor]
            cursor += 1
            left = pixels[row + x - bpp] if x >= bpp else 0
            up = pixels[row - stride + x] if y else 0
            up_left = pixels[row - stride + x - bpp] if y and x >= bpp else 0
            if filt == 1:
                value += left
            elif filt == 2:
                value += up
            elif filt == 3:
                value += (left + up) // 2
            elif filt == 4:
                value += paeth(left, up, up_left)
            elif filt != 0:
                raise ValueError(f"unknown PNG filter {filt}")
            pixels[row + x] = value & 255
    return width, height, bytes(pixels)


def crop_rgb(width, height, pixels, roi):
    if roi["x"] < 0 or roi["y"] < 0 or roi["x"] + roi["width"] > width or roi["y"] + roi["height"] > height:
        raise ValueError("ROI out of bounds")
    stride = width * 3
    row_bytes = roi["width"] * 3
    return b"".join(
        pixels[(roi["y"] + y) * stride + roi["x"] * 3:(roi["y"] + y) * stride + roi["x"] * 3 + row_bytes]
        for y in range(roi["height"])
    )


def expected_row(frame, source, crop_bytes, manifest):
    width, height, pixels = decode_png(source)
    if (width, height) != (frame["width"], frame["height"]):
        raise ValueError("source dimensions mismatch")
    if sha(source) != frame["png_sha256"] or sha(pixels) != frame["source_pixel_sha256"]:
        raise ValueError("source identity mismatch")
    crop_width, crop_height, crop_pixels = decode_png(crop_bytes)
    roi_pixels = crop_rgb(width, height, pixels, manifest["roi"])
    if (crop_width, crop_height) != (manifest["roi"]["width"], manifest["roi"]["height"]):
        raise ValueError("crop dimensions mismatch")
    if crop_pixels != roi_pixels:
        raise ValueError("crop pixel mismatch")
    full_payload = {
        "frame_id": frame["frame_id"],
        "mode": "FULL_FRAME",
        "png_base64": __import__("base64").b64encode(source).decode("ascii"),
        "sequence": frame["sequence"],
        "source_pixel_sha256": frame["source_pixel_sha256"],
    }
    focused_payload = {
        "focus": {
            "height": manifest["roi"]["height"],
            "reason": "post_input_text_state_tracking",
            "width": manifest["roi"]["width"],
            "x": manifest["roi"]["x"],
            "y": manifest["roi"]["y"],
        },
        "frame_id": frame["frame_id"],
        "mode": "FOCUSED_REGION",
        "png_base64": __import__("base64").b64encode(crop_bytes).decode("ascii"),
        "sequence": frame["sequence"],
        "source_pixel_sha256": frame["source_pixel_sha256"],
    }
    return {
        "crop_file": f"artifacts/{frame['sequence']}.png",
        "crop_png_sha256": sha(crop_bytes),
        "crop_pixel_sha256": sha(roi_pixels),
        "focused_payload_bytes": len(canonical(focused_payload)),
        "frame_id": frame["frame_id"],
        "full_payload_bytes": len(canonical(full_payload)),
        "roi_pixel_sha256": sha(roi_pixels),
        "sequence": frame["sequence"],
        "source_png_sha256": sha(source),
        "source_pixel_sha256": frame["source_pixel_sha256"],
    }


def validate(candidate, manifest, package_root, image_root=IMAGE_ROOT):
    errors = []
    try:
        if candidate.get("allocation") != manifest["allocation"]:
            errors.append("allocation identity mismatch")
        frames = manifest["frames"]
        rows = candidate.get("rows")
        if not isinstance(rows, list) or len(rows) != len(frames):
            return errors + ["row count mismatch"]
        expected = []
        for frame, row in zip(frames, rows):
            expected_path = f"artifacts/{frame['sequence']}.png"
            if not isinstance(row, dict) or row.get("crop_file") != expected_path:
                errors.append(f"crop path/order mismatch at sequence {frame['sequence']}")
                continue
            source = (image_root / frame["file"]).read_bytes()
            crop_bytes = (package_root / "results" / expected_path).read_bytes()
            expected.append(expected_row(frame, source, crop_bytes, manifest))
            if row != expected[-1]:
                errors.append(f"row does not match independent reconstruction at sequence {frame['sequence']}")
        if len(expected) != len(frames):
            return errors + ["independent reconstruction incomplete"]
        summary = {
            "distinct_roi_states": len({r["roi_pixel_sha256"] for r in expected}),
            "focused_payload_bytes": sum(r["focused_payload_bytes"] for r in expected),
            "full_frame_payload_bytes": sum(r["full_payload_bytes"] for r in expected),
            "saved_bytes": sum(r["full_payload_bytes"] - r["focused_payload_bytes"] for r in expected),
        }
        if candidate.get("summary") != summary:
            errors.append("summary does not match independent reconstruction")
    except Exception as exc:  # audit must retain a bounded diagnostic, not conceal a raw mismatch
        errors.append(f"raw audit exception: {type(exc).__name__}: {exc}")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    args = parser.parse_args()
    package = args.package.resolve()
    manifest = json.loads((package / "manifest.json").read_text())
    candidate = json.loads((package / "results" / "candidate.json").read_text())
    errors = validate(candidate, manifest, package)
    mutations = []
    for name, mutate in [
        ("sequence", lambda x: x["rows"][0].__setitem__("sequence", 99)),
        ("crop_path", lambda x: x["rows"][0].__setitem__("crop_file", "../escape.png")),
        ("crop_digest", lambda x: x["rows"][0].__setitem__("crop_png_sha256", "0" * 64)),
        ("payload_count", lambda x: x["rows"][0].__setitem__("focused_payload_bytes", 0)),
        ("summary", lambda x: x["summary"].__setitem__("saved_bytes", -1)),
        ("source_pixels", lambda x: x["rows"][0].__setitem__("source_pixel_sha256", "f" * 64)),
    ]:
        changed = copy.deepcopy(candidate)
        mutate(changed)
        rejected = bool(validate(changed, manifest, package))
        mutations.append({"mutation": name, "rejected": rejected})
    mutation_rejections = sum(item["rejected"] for item in mutations)
    rows = candidate.get("rows", [])
    all_smaller = len(rows) == 3 and all(r.get("focused_payload_bytes", 0) < r.get("full_payload_bytes", 0) for r in rows)
    unique_states = candidate.get("summary", {}).get("distinct_roi_states") == 3
    disposition = "PASS_METHOD_SCOPED" if not errors and all_smaller and unique_states and mutation_rejections == 6 else "FAIL"
    report = {
        "allocation": manifest["allocation"],
        "disposition": disposition,
        "independent_reconstruction": "PASS" if not errors else "FAIL",
        "mutation_controls": mutations,
        "mutation_rejections": mutation_rejections,
        "errors": errors,
        "rows": len(rows),
        "all_focused_payloads_strictly_smaller": all_smaller,
        "three_distinct_roi_states": unique_states,
        "scope": "one archived Chromium trace; exact temporal ROI pixel preservation and serialized JSON byte accounting only",
    }
    target = package / "results" / "audit.json"
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))
    return 0 if disposition == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    sys.exit(main())
