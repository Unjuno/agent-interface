"""Pack verified tooltip receipts without repeating the full source frame."""
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw


def sha_pixels(image):
    return hashlib.sha256(image.convert("RGB").tobytes()).hexdigest()


def build(readiness, runtime_dir, destination, scale=2):
    if (not isinstance(readiness, dict) or readiness.get("status") != "READY"
            or not readiness.get("receipts")):
        raise ValueError("verified hover readiness required")
    if type(scale) is not int or not 1 <= scale <= 4:
        raise ValueError("integer display scale from one to four required")
    runtime_dir = Path(runtime_dir)
    events = [json.loads(line) for line in
              (runtime_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    observations = {row["sequence"]: row for row in events
                    if row.get("event") == "observation"}
    rows = []
    for receipt in readiness["receipts"]:
        observation = observations.get(receipt["dwell_sequence"])
        if observation is None:
            raise ValueError("receipt dwell observation missing")
        with Image.open(runtime_dir / Path(observation["image"]).name) as opened:
            frame = opened.convert("RGB")
        tooltip = frame.crop(tuple(receipt["tooltip"]["box"]))
        digest = sha_pixels(tooltip)
        if digest != receipt["tooltip"]["pixels_sha256"]:
            raise ValueError("receipt tooltip pixels do not match runtime observation")
        rows.append((receipt, tooltip, digest))

    row_height = 62
    width = 640
    sheet = Image.new("RGB", (width, 24 + row_height * len(rows)), "black")
    draw = ImageDraw.Draw(sheet)
    draw.text((6, 6), "verified persistent hover receipts", fill="white")
    manifest_rows = []
    for row_index, (receipt, tooltip, digest) in enumerate(rows):
        y = 24 + row_index * row_height
        label = (f'receipt {receipt["receipt_index"]}  point '
                 f'({receipt["point"][0]}, {receipt["point"][1]})')
        draw.text((6, y + 4), label, fill="white")
        displayed = tooltip.resize(
            (tooltip.width * scale, tooltip.height * scale), Image.Resampling.NEAREST)
        if displayed.width > width - 230 or displayed.height > row_height - 4:
            raise ValueError("displayed tooltip exceeds compact row")
        sheet.paste(displayed, (225, y + 2))
        manifest_rows.append({
            "receipt_index": receipt["receipt_index"],
            "point": receipt["point"],
            "dwell_sequence": receipt["dwell_sequence"],
            "persistent_sequence": receipt["persistent_sequence"],
            "raw_tooltip_sha256": digest,
            "raw_size": list(tooltip.size),
            "display_scale": scale,
            "display_filter": "nearest",
        })
    destination = Path(destination)
    sheet.save(destination)
    return {"path": str(destination), "size": list(sheet.size),
            "pixels_sha256": sha_pixels(sheet), "rows": manifest_rows,
            "omitted": "full source frame and non-tooltip pixels",
            "authority": "presentation only; original verified receipts remain authoritative"}
