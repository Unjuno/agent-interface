#!/usr/bin/env python3
"""Independent standard-library raw-only auditor for Pillow PNG payload bytes."""
from __future__ import annotations

import base64
import binascii
import copy
import hashlib
import json
import struct
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ALLOCATION = "LABEL-CONTROL-AMBIGUITY-1998-T0-A04-20261009"
BASE = "4758a95cd4a0aaa78e9cdc9d774f298d4ccf0e36"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def resolve_repo(path: str) -> Path:
    return REPO / path


def decode_png(data: bytes) -> tuple[int, int, bytes]:
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("png signature")
    pos = len(PNG_SIGNATURE)
    ihdr = None
    idat_parts = []
    saw_idat = False
    ended_idat = False
    saw_iend = False
    while pos < len(data):
        if pos + 12 > len(data):
            raise ValueError("truncated PNG chunk")
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        stop = pos + 12 + length
        if stop > len(data):
            raise ValueError("PNG chunk length")
        body = data[pos + 8:pos + 8 + length]
        crc = struct.unpack(">I", data[pos + 8 + length:stop])[0]
        if (binascii.crc32(kind + body) & 0xFFFFFFFF) != crc:
            raise ValueError("PNG CRC")
        if pos == len(PNG_SIGNATURE) and kind != b"IHDR":
            raise ValueError("IHDR must be first")
        if kind == b"IHDR":
            if ihdr is not None or length != 13:
                raise ValueError("duplicate or malformed IHDR")
            ihdr = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT":
            if ended_idat:
                raise ValueError("nonconsecutive IDAT")
            saw_idat = True
            idat_parts.append(body)
        elif kind == b"IEND":
            if length != 0 or saw_iend:
                raise ValueError("malformed IEND")
            saw_iend = True
            pos = stop
            if pos != len(data):
                raise ValueError("trailing PNG bytes")
            break
        else:
            if saw_idat:
                ended_idat = True
            # Unknown critical chunks change image interpretation and are refused.
            if kind and 65 <= kind[0] <= 90 and kind not in (b"PLTE",):
                raise ValueError("unsupported critical PNG chunk")
        pos = stop
    if not saw_iend or not saw_idat or not idat_parts or ihdr is None:
        raise ValueError("incomplete PNG")
    width, height, depth, color, compression, filtering, interlace = ihdr
    if not width or not height or (depth, color, compression, filtering, interlace) != (8, 2, 0, 0, 0):
        raise ValueError("unsupported PNG profile")
    decoder = zlib.decompressobj()
    packed = decoder.decompress(b"".join(idat_parts)) + decoder.flush()
    if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        raise ValueError("PNG deflate termination")
    stride = width * 3
    if len(packed) != height * (stride + 1):
        raise ValueError("PNG decoded length")
    rows = []
    previous = bytearray(stride)
    for y in range(height):
        offset = y * (stride + 1)
        filter_type = packed[offset]
        source = packed[offset + 1:offset + 1 + stride]
        current = bytearray(stride)
        for index, value in enumerate(source):
            left = current[index - 3] if index >= 3 else 0
            up = previous[index]
            upper_left = previous[index - 3] if index >= 3 else 0
            if filter_type == 0:
                predictor = 0
            elif filter_type == 1:
                predictor = left
            elif filter_type == 2:
                predictor = up
            elif filter_type == 3:
                predictor = (left + up) // 2
            elif filter_type == 4:
                p = left + up - upper_left
                pa, pb, pc = abs(p - left), abs(p - up), abs(p - upper_left)
                predictor = left if pa <= pb and pa <= pc else up if pb <= pc else upper_left
            else:
                raise ValueError("unknown PNG filter")
            current[index] = (value + predictor) & 0xFF
        rows.append(bytes(current))
        previous = current
    return width, height, b"".join(rows)


def pixel_digest(width: int, height: int, pixels: bytes) -> str:
    return sha(f"{width},{height},RGB:".encode("ascii") + pixels)


def roi_bounds(width: int, height: int, crop_width: int, crop_height: int, placement: str) -> list[int]:
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
    result = []
    for area_id, size in design["area_sizes_pixels"].items():
        crop_width, crop_height = size
        for placement in design["placements"]:
            bounds = roi_bounds(width, height, crop_width, crop_height, placement)
            region_id = f"{area_id}-{placement}"
            result.append({
                "case_id": f"{frame['frame_id']}__{area_id}__{placement}",
                "frame_id": frame["frame_id"],
                "request": {"frame_id": frame["frame_id"], "epoch": frame["epoch"],
                            "region_id": region_id, "candidate_region_ids": [region_id],
                            "reason": "uncertain", "bounds": bounds},
                "crop_width": crop_width, "crop_height": crop_height,
            })
    region_id = "full-bounds-control"
    result.append({
        "case_id": f"{frame['frame_id']}__full_bounds_control",
        "frame_id": frame["frame_id"],
        "request": {"frame_id": frame["frame_id"], "epoch": frame["epoch"],
                    "region_id": region_id, "candidate_region_ids": [region_id],
                    "reason": "uncertain", "bounds": [0, 0, width, height]},
        "crop_width": width, "crop_height": height,
    })
    return result


def make_payload(frame: dict, width: int, height: int, png: bytes, kind: str,
                 request: dict | None = None) -> dict:
    value = {"schema": "focused-observation-png-v1", "kind": kind,
             "media_type": "image/png", "frame_id": frame["frame_id"],
             "epoch": frame["epoch"], "width": width, "height": height,
             "encoding": "RGB8", "png_b64": base64.b64encode(png).decode("ascii")}
    if request is not None:
        value.update({"region_id": request["region_id"], "bounds": request["bounds"],
                      "reason": request["reason"]})
    return value


def source_pixels(design: dict) -> dict[str, bytes]:
    ledger_rows = {}
    for ledger in design["inputs"]:
        ledger_data = resolve_repo(ledger["path"]).read_bytes()
        if sha(ledger_data) != ledger["sha256"]:
            raise ValueError("observation ledger bytes changed:" + ledger["path"])
        app = Path(ledger["path"]).parent.name.split("-1101-O0", 1)[0]
        for line in ledger_data.decode("utf-8").splitlines():
            row = json.loads(line)
            ledger_rows.setdefault((app, row["sha256"]), row)
    if len(ledger_rows) != len(design["frames"]):
        raise ValueError("ledger-to-frame coverage")
    result = {}
    for frame in design["frames"]:
        ledger = ledger_rows.get((frame["application"], frame["source_pixel_sha256"]))
        if (ledger is None or frame["epoch"] != ledger["sequence"]
                or frame["ledger_sequence"] != ledger["sequence"]
                or frame["first_action_id"] != ledger["action_id"]):
            raise ValueError("frame-to-ledger identity:" + frame["frame_id"])
        data = resolve_repo(frame["source_png_path"]).read_bytes()
        if sha(data) != frame["source_png_sha256"]:
            raise ValueError("source PNG bytes changed:" + frame["frame_id"])
        width, height, pixels = decode_png(data)
        if (width, height) != (1280, 800) or pixel_digest(width, height, pixels) != frame["source_pixel_sha256"]:
            raise ValueError("source pixel identity:" + frame["frame_id"])
        result[frame["frame_id"]] = pixels
    return result


def validate(raw: object, design: dict, pixels: dict[str, bytes], artifacts: dict[str, bytes]) -> list[str]:
    errors = []
    if not isinstance(raw, dict) or raw.get("schema") != "1998-a04-pillow-png-payload-raw-v1":
        return ["raw schema"]
    freeze_sha = sha((HERE / "FREEZE.json").read_bytes())
    if (raw.get("allocation") != ALLOCATION or raw.get("base_commit") != BASE
            or raw.get("freeze_sha256") != freeze_sha
            or raw.get("pillow_version") != "12.3.0" or raw.get("compress_level") != 6):
        errors.append("raw identity or encoder settings")
    frames = raw.get("frames")
    expected_frame_ids = [frame["frame_id"] for frame in design["frames"]]
    if (not isinstance(frames, list) or raw.get("frame_count") != len(expected_frame_ids)
            or [item.get("frame_id") for item in frames] != expected_frame_ids):
        return errors + ["frame coverage/order"]
    frame_map = {frame["frame_id"]: frame for frame in design["frames"]}
    full_meta = {}
    for frame_record in frames:
        frame = frame_map[frame_record["frame_id"]]
        full_path = frame_record.get("full_png_path")
        expected_path = f"results/artifacts/full/{frame['frame_id']}/frame.png"
        png = artifacts.get(full_path, b"")
        try:
            if full_path != expected_path or sha(png) != frame_record.get("full_png_sha256"):
                raise ValueError("full artifact path/hash")
            width, height, decoded = decode_png(png)
            if (width, height) != (1280, 800) or decoded != pixels[frame["frame_id"]]:
                raise ValueError("full frame reconstruction")
            payload = make_payload(frame, width, height, png, "FULL_FRAME")
            if (frame_record.get("source_pixel_sha256") != frame["source_pixel_sha256"]
                    or frame_record.get("full_png_bytes") != len(png)
                    or frame_record.get("full_payload_bytes") != len(canonical(payload))):
                raise ValueError("full frame accounting/identity")
            full_meta[frame["frame_id"]] = (payload, len(canonical(payload)))
        except Exception as exc:
            errors.append(frame["frame_id"] + ":" + str(exc))
    rows = raw.get("rows")
    wanted = [case for frame in design["frames"]
              for case in expected_cases(frame, 1280, 800, design)]
    if (not isinstance(rows, list) or raw.get("case_count") != len(wanted)
            or len(rows or []) != len(wanted)):
        return errors + ["case coverage"]
    if [row.get("case_id") for row in rows] != [case["case_id"] for case in wanted]:
        errors.append("case identities/order")
    for index, case in enumerate(wanted):
        row = rows[index]
        frame = frame_map[case["frame_id"]]
        source = pixels[frame["frame_id"]]
        full_payload, full_payload_size = full_meta.get(frame["frame_id"], ({}, -1))
        focus_path = row.get("focus_png_path")
        expected_path = f"results/artifacts/crops/{case['case_id']}/crop.png"
        crop_png = artifacts.get(focus_path, b"")
        try:
            if (row.get("frame_id") != case["frame_id"] or row.get("request") != case["request"]
                    or row.get("case_id") != case["case_id"]):
                raise ValueError("case/request/frame identity")
            if focus_path != expected_path or sha(crop_png) != row.get("focus_png_sha256"):
                raise ValueError("crop artifact path/hash")
            x0, y0, x1, y1 = case["request"]["bounds"]
            crop_width, crop_height, crop_pixels = decode_png(crop_png)
            expected_pixels = b"".join(
                source[(y * 1280 + x0) * 3:(y * 1280 + x1) * 3]
                for y in range(y0, y1)
            )
            if (crop_width, crop_height) != (x1 - x0, y1 - y0) or crop_pixels != expected_pixels:
                raise ValueError("crop pixel reconstruction")
            focused_payload = make_payload(frame, crop_width, crop_height, crop_png,
                                           "FOCUSED_REGION", case["request"])
            focused_size = len(canonical(focused_payload))
            use_focus = focused_size < full_payload_size
            selected_kind = "FOCUSED_REGION" if use_focus else "FULL_FRAME"
            selected_size = focused_size if use_focus else full_payload_size
            decision = "FOCUSED_REGION_SELECTED" if use_focus else "FULL_FRAME_NO_SIZE_GAIN"
            if (row.get("crop_width") != crop_width or row.get("crop_height") != crop_height
                    or row.get("focus_png_bytes") != len(crop_png)
                    or row.get("focus_payload_bytes") != focused_size
                    or row.get("full_payload_bytes") != full_payload_size
                    or row.get("selected_kind") != selected_kind
                    or row.get("selected_payload_bytes") != selected_size
                    or row.get("bytes_saved_vs_full") != full_payload_size - selected_size
                    or row.get("decision") != decision):
                raise ValueError("serialized byte/selection accounting")
            if case["case_id"].endswith("__full_bounds_control") and selected_kind != "FULL_FRAME":
                raise ValueError("full-bounds control did not fall back")
        except Exception as exc:
            errors.append(case["case_id"] + ":" + str(exc))
    return errors


def read_artifacts(raw: dict) -> dict[str, bytes]:
    paths = [frame["full_png_path"] for frame in raw.get("frames", [])]
    paths += [row["focus_png_path"] for row in raw.get("rows", [])]
    return {path: (HERE / path).read_bytes() for path in set(paths)}


def audit(raw: dict, design: dict) -> dict:
    pixels = source_pixels(design)
    artifacts = read_artifacts(raw)
    errors = validate(raw, design, pixels, artifacts)
    mutation_results = []

    def check(name: str, mutate) -> None:
        changed_raw = copy.deepcopy(raw)
        changed_artifacts = dict(artifacts)
        mutate(changed_raw, changed_artifacts)
        mutation_results.append({"name": name,
                                 "rejected": bool(validate(changed_raw, design, pixels, changed_artifacts))})

    first_crop = raw["rows"][0]["focus_png_path"]

    def corrupt_png(value, files):
        data = bytearray(files[first_crop])
        data[-5] ^= 1
        files[first_crop] = bytes(data)

    check("crop_png_crc_corruption", corrupt_png)
    check("source_pixel_identity_tamper", lambda value, files: value["frames"][0].__setitem__("source_pixel_sha256", "0" * 64))
    check("region_bounds_tamper", lambda value, files: value["rows"][0]["request"]["bounds"].__setitem__(0, 1))
    check("serialized_byte_count_tamper", lambda value, files: value["rows"][0].__setitem__("focus_payload_bytes", 1))
    full_control_index = next(i for i, row in enumerate(raw["rows"]) if row["case_id"].endswith("__full_bounds_control"))
    check("full_bounds_control_forced_to_focus", lambda value, files: value["rows"][full_control_index].__setitem__("selected_kind", "FOCUSED_REGION"))
    check("missing_case", lambda value, files: value["rows"].pop())

    rows = raw.get("rows", [])
    crop_rows = [row for row in rows if not row["case_id"].endswith("__full_bounds_control")]
    focus_count = sum(row.get("selected_kind") == "FOCUSED_REGION" for row in rows)
    fallback_count = sum(row.get("selected_kind") == "FULL_FRAME" for row in rows)
    positive = sum(row.get("bytes_saved_vs_full", 0) > 0 for row in crop_rows)
    full_bounds_fallbacks = sum(
        row.get("selected_kind") == "FULL_FRAME"
        for row in rows if row["case_id"].endswith("__full_bounds_control")
    )
    mutation_pass = len(mutation_results) == 6 and all(item["rejected"] for item in mutation_results)
    passed = not errors and mutation_pass and positive > 0 and full_bounds_fallbacks == 21
    status = "PASS_METHOD_SCOPED" if passed else "HOLD_NO_SIZE_GAIN" if not errors and mutation_pass and positive == 0 else "FAIL_METHOD"
    return {
        "schema": "1998-a04-pillow-png-audit-v1", "allocation": ALLOCATION,
        "status": status,
        "case_count": len(rows), "frame_count": len(raw.get("frames", [])),
        "focus_selected": focus_count, "fallback_full_frame": fallback_count,
        "valid_crop_cases_with_positive_savings": positive,
        "full_bounds_controls_fallback": full_bounds_fallbacks,
        "baseline_full_payload_bytes_repeated_per_case": sum(row.get("full_payload_bytes", 0) for row in rows),
        "selected_payload_bytes": sum(row.get("selected_payload_bytes", 0) for row in rows),
        "bytes_saved_vs_full": sum(row.get("bytes_saved_vs_full", 0) for row in rows),
        "mutations_rejected": sum(item["rejected"] for item in mutation_results),
        "mutations_total": len(mutation_results), "mutation_results": mutation_results,
        "errors": errors,
        "scope": "Finite serialized-byte accounting on retained GUI PNG frames using main ImageArtifactSink and Pillow 12.3.0; no ROI-quality, model, token, latency, live GUI, authority, task-effect, or product claim.",
    }


def main() -> int:
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    for key, expected in freeze["source_sha256"].items():
        path = REPO / key[len("repo/"):] if key.startswith("repo/") else HERE / key[len("package/"):]
        if sha(path.read_bytes()) != expected:
            raise SystemExit("STOP_SOURCE_HASH:" + key)
    design = json.loads((HERE / "design.json").read_text(encoding="utf-8"))
    raw = json.loads((HERE / "results" / "candidate.stdout").read_text(encoding="utf-8"))
    result = audit(raw, design)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["status"] == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
