#!/usr/bin/env python3
"""Independent raw-only auditor for canonical PNG crop payloads."""
import base64
import binascii
import copy
import hashlib
import json
import struct
import sys
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


def decode_png(data: bytes) -> tuple[int, int, bytes]:
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("signature")
    pos = len(PNG_SIGNATURE)
    chunks = []
    while pos < len(data):
        if pos + 12 > len(data):
            raise ValueError("truncated chunk")
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        end = pos + 12 + length
        if end > len(data):
            raise ValueError("chunk length")
        payload = data[pos + 8:pos + 8 + length]
        expected_crc = struct.unpack(">I", data[pos + 8 + length:end])[0]
        if (binascii.crc32(kind + payload) & 0xFFFFFFFF) != expected_crc:
            raise ValueError("crc")
        chunks.append((kind, payload))
        pos = end
        if kind == b"IEND":
            if pos != len(data):
                raise ValueError("trailing bytes")
            break
    if [kind for kind, _ in chunks] != [b"IHDR", b"IDAT", b"IEND"]:
        raise ValueError("chunk order or unexpected chunk")
    ihdr = chunks[0][1]
    if len(ihdr) != 13:
        raise ValueError("ihdr length")
    width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", ihdr)
    if not width or not height or (depth, color, compression, filtering, interlace) != (8, 2, 0, 0, 0):
        raise ValueError("unsupported PNG profile")
    decoder = zlib.decompressobj()
    packed = decoder.decompress(chunks[1][1]) + decoder.flush()
    if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        raise ValueError("deflate termination")
    stride = width * 3
    if len(packed) != height * (stride + 1):
        raise ValueError("decoded length")
    rows = []
    for y in range(height):
        start = y * (stride + 1)
        if packed[start] != 0:
            raise ValueError("nonzero filter")
        rows.append(packed[start + 1:start + 1 + stride])
    return width, height, b"".join(rows)


def crop_rgb(source: bytes, width: int, bounds: list[int]) -> tuple[int, int, bytes]:
    x0, y0, x1, y1 = bounds
    out_width = x1 - x0
    return out_width, y1 - y0, b"".join(
        source[(y * width + x0) * 3:(y * width + x1) * 3]
        for y in range(y0, y1)
    )


def load_inputs() -> tuple[dict, dict[str, bytes], dict[str, dict]]:
    freeze = json.loads((ROOT / "FREEZE.json").read_text())
    if freeze["allocation"] != ALLOCATION or freeze["base_commit"] != BASE:
        raise ValueError("freeze identity/base mismatch")
    for name, expected in freeze["source_sha256"].items():
        if sha(ROOT / name) != expected:
            raise ValueError("frozen source mismatch: " + name)
    design = json.loads((ROOT / "design.json").read_text())
    sources = {frame["frame_id"]: (ROOT / frame["source"]).read_bytes()
               for frame in design["frames"]}
    frames = {frame["frame_id"]: frame for frame in design["frames"]}
    return design, sources, frames


def refuse(request: dict, frame: dict, width: int, height: int) -> str | None:
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
    if (len(bounds) != 4 or any(type(value) is not int for value in bounds)
            or not (0 <= bounds[0] < bounds[2] <= width and 0 <= bounds[1] < bounds[3] <= height)):
        return "REGION_OUT_OF_BOUNDS"
    return None


def expected_requests(design: dict) -> list[tuple[str, dict, dict, bool]]:
    out = []
    for frame in design["frames"]:
        for roi in design["valid_rois"]:
            request = {"reason": "uncertain", "frame_id": frame["frame_id"],
                       "epoch": frame["epoch"], "focus_state": "active",
                       "region_id": roi["roi_id"], "candidate_region_ids": [roi["roi_id"]],
                       "bounds": roi["bounds"]}
            out.append((frame["pattern"] + ":" + roi["roi_id"], request, frame, True))
    frame = design["frames"][0]
    for item in design["invalid_requests"]:
        request = {key: value for key, value in item.items() if key != "case_id"}
        out.append((item["case_id"], request, frame, False))
    return out


def full_payload(frame: dict, width: int, height: int, pixels: bytes, payload: dict) -> None:
    if payload != {"schema": "focused-observation-png-v1", "kind": "FULL_FRAME",
                   "media_type": "image/png", "frame_id": frame["frame_id"],
                   "epoch": frame["epoch"], "width": width, "height": height,
                   "encoding": "RGB8", "png_b64": payload.get("png_b64")}:
        raise ValueError("full metadata")
    png = base64.b64decode(payload["png_b64"], validate=True)
    decoded = decode_png(png)
    if decoded != (width, height, pixels):
        raise ValueError("full pixels")


def validate(raw: object, design: dict, sources: dict[str, bytes], frames: dict[str, dict]) -> list[str]:
    errors = []
    if not isinstance(raw, dict) or raw.get("schema") != "1998-a03-png-payload-raw-v1":
        return ["raw schema"]
    if raw.get("allocation") != ALLOCATION or raw.get("base_commit") != BASE:
        errors.append("identity")
    rows = raw.get("rows")
    wanted = expected_requests(design)
    if not isinstance(rows, list) or raw.get("case_count") != len(wanted) or len(rows or []) != len(wanted):
        return errors + ["coverage"]
    if [row.get("case_id") for row in rows] != [item[0] for item in wanted]:
        errors.append("case identities/order")
    width, height = design["width"], design["height"]
    for index, (case_id, request, frame, valid) in enumerate(wanted):
        row = rows[index]
        source = sources[frame["frame_id"]]
        expected_full = row.get("full_frame_payload")
        try:
            full_payload(frame, width, height, source, expected_full)
            full_bytes = len(canonical(expected_full))
            if row.get("request") != request or row.get("full_frame_bytes") != full_bytes:
                raise ValueError("request/full byte count")
            if valid:
                if refuse(request, frame, width, height) is not None:
                    raise ValueError("unexpected request refusal")
                crop_width, crop_height, expected_crop = crop_rgb(source, width, request["bounds"])
                focus = row.get("focused_payload")
                expected_meta = {"schema": "focused-observation-png-v1", "kind": "FOCUSED_REGION",
                                 "media_type": "image/png", "frame_id": frame["frame_id"],
                                 "epoch": frame["epoch"], "width": crop_width, "height": crop_height,
                                 "encoding": "RGB8", "region_id": request["region_id"],
                                 "bounds": request["bounds"], "reason": request["reason"]}
                if not isinstance(focus, dict) or any(focus.get(k) != v for k, v in expected_meta.items()):
                    raise ValueError("focus metadata")
                crop_png = base64.b64decode(focus["png_b64"], validate=True)
                if decode_png(crop_png) != (crop_width, crop_height, expected_crop):
                    raise ValueError("crop pixels")
                focus_bytes = len(canonical(focus))
                if row.get("focused_bytes") != focus_bytes:
                    raise ValueError("focus byte count")
                focus_selected = focus_bytes < full_bytes
                chosen_kind = "FOCUSED_REGION" if focus_selected else "FULL_FRAME"
                chosen_payload = focus if focus_selected else expected_full
                decision = "FOCUSED_REGION_SELECTED" if focus_selected else "FULL_FRAME_NO_SIZE_GAIN"
                if row.get("focused_bytes") is None:
                    raise ValueError("missing focus byte count")
            else:
                reason = refuse(request, frame, width, height)
                if reason is None or row.get("focused_payload") is not None or row.get("focused_bytes") is not None:
                    raise ValueError("invalid request crop emitted")
                focus_selected = False
                chosen_kind, chosen_payload = "FULL_FRAME", expected_full
                decision = "ABSTAIN_" + reason
            if (row.get("selected_kind") != chosen_kind or row.get("selected_payload") != chosen_payload
                    or row.get("selected_bytes") != len(canonical(chosen_payload))
                    or row.get("bytes_saved_vs_full") != full_bytes - len(canonical(chosen_payload))
                    or row.get("decision") != decision):
                raise ValueError("selection/serialized byte accounting")
        except Exception as exc:
            errors.append(case_id + ":" + str(exc))
    return errors


def main() -> int:
    design, sources, frames = load_inputs()
    raw = json.loads((ROOT / "results" / "candidate_raw.json").read_text())
    errors = validate(raw, design, sources, frames)
    rows = raw.get("rows", []) if isinstance(raw, dict) else []
    valid_rows = rows[:len(design["frames"]) * len(design["valid_rois"])]
    savings = [row["bytes_saved_vs_full"] for row in valid_rows]
    selected_count = sum(row["selected_kind"] == "FOCUSED_REGION" for row in valid_rows)
    fallback_count = sum(row["selected_kind"] == "FULL_FRAME" for row in valid_rows)
    mutation_rows = []

    def check_mutation(name: str, mutate) -> None:
        altered = copy.deepcopy(raw)
        mutate(altered)
        mutation_rows.append({"name": name, "rejected": bool(validate(altered, design, sources, frames))})

    def flip_focus_png(value: dict) -> None:
        png = bytearray(base64.b64decode(value["rows"][0]["focused_payload"]["png_b64"]))
        png[-5] ^= 1
        value["rows"][0]["focused_payload"]["png_b64"] = base64.b64encode(png).decode("ascii")

    check_mutation("png_crc_corruption", flip_focus_png)
    check_mutation("focus_region_identity_swap", lambda value: value["rows"][0]["focused_payload"].__setitem__("region_id", "other"))
    check_mutation("stale_request_selected_as_focus", lambda value: value["rows"][18].__setitem__("selected_kind", "FOCUSED_REGION"))
    check_mutation("out_of_bounds_request_selected_as_focus", lambda value: value["rows"][22].__setitem__("selected_kind", "FOCUSED_REGION"))
    check_mutation("full_frame_no_gain_focus_selected", lambda value: value["rows"][4].__setitem__("selected_kind", "FOCUSED_REGION"))
    check_mutation("serialized_byte_count_tamper", lambda value: value["rows"][0].__setitem__("selected_bytes", 1))
    mutations_rejected = sum(item["rejected"] for item in mutation_rows)
    positive = sum(value > 0 for value in savings)
    no_gain_full = sum(row["decision"] == "FULL_FRAME_NO_SIZE_GAIN" for row in valid_rows)
    if len(mutation_rows) != 6 or mutations_rejected != 6:
        errors.append("mutation controls")
    if not errors and (positive < 1 or no_gain_full < 1 or selected_count + fallback_count != 18):
        errors.append("preregistered economic boundary")
    summary = {
        "schema": "1998-a03-png-payload-audit-v1", "allocation": ALLOCATION,
        "status": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD",
        "decision": "SUPPORT_FOR_PNG_CROP_PAYLOAD_REDUCTION_SCOPED" if not errors else "FAIL_METHOD",
        "case_count": len(rows), "valid_cases": len(valid_rows), "invalid_cases": len(rows) - len(valid_rows),
        "valid_focus_selected": selected_count, "valid_full_frame_fallback": fallback_count,
        "valid_cases_with_positive_savings": positive, "valid_no_gain_fallbacks": no_gain_full,
        "full_frame_total_bytes": sum(row["full_frame_bytes"] for row in rows),
        "selected_total_bytes": sum(row["selected_bytes"] for row in rows),
        "selected_total_bytes_saved": sum(row["bytes_saved_vs_full"] for row in rows),
        "mutations_rejected": mutations_rejected, "mutations_total": len(mutation_rows),
        "mutation_results": mutation_rows, "errors": errors,
        "scope": "Synthetic canonical PNG crop accounting only; no codec timing, tokens, GUI, model, or task effect claim."
    }
    print(json.dumps(summary, sort_keys=True, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
