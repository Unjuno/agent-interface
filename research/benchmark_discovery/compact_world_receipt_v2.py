"""Build normal or deterministically unreadable Mindustry world evidence."""
import hashlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageStat


def build(readiness, runtime_dir, output, presentation="normal"):
    if readiness.get("status") != "READY" or len(readiness.get("receipts", [])) != 1:
        raise ValueError("one ready world receipt required")
    if presentation not in ("normal", "unreadable"):
        raise ValueError("unknown world receipt presentation")
    receipt = readiness["receipts"][0]
    evidence = receipt["evidence"]
    runtime_dir = Path(runtime_dir)
    sequence = receipt["dwell_sequences"][-1]
    source = runtime_dir / receipt["last_image"]
    with Image.open(source) as opened:
        crop = opened.convert("RGB").crop(tuple(evidence["box"]))
    if hashlib.sha256(crop.tobytes()).hexdigest() != evidence["last_pixels_sha256"]:
        raise ValueError("world evidence crop digest mismatch")
    scale = min(3, 360 // crop.width, 240 // crop.height)
    if scale < 1:
        raise ValueError("world receipt exceeds presentation bounds")
    shown = crop.resize((crop.width * scale, crop.height * scale), Image.Resampling.NEAREST)
    if presentation == "unreadable":
        mean = tuple(round(value) for value in ImageStat.Stat(shown).mean)
        shown = Image.new("RGB", shown.size, mean)
    canvas = Image.new("RGB", (640, max(120, shown.height + 34)), "white")
    draw = ImageDraw.Draw(canvas)
    point = receipt["point"]
    draw.text((8, 6), f"RECEIPT 1  POINT [{point[0]},{point[1]}]  FRAMES {len(receipt['dwell_sequences'])}", fill="black")
    label = ("stable animated placement-preview mask; observation evidence only" if presentation == "normal"
             else "receipt pixels unavailable; printed point alone does not prove the relation")
    draw.text((8, 20), label, fill="black")
    canvas.paste(shown, (8, 34))
    canvas.save(output)
    return {
        "size": list(canvas.size), "scale": scale, "crop_size": list(crop.size),
        "source_sequence": sequence, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "source_pixels_sha256": hashlib.sha256(crop.tobytes()).hexdigest(),
        "presentation": presentation,
        "presentation_sha256": hashlib.sha256(canvas.tobytes()).hexdigest(),
        "authority": "presentation only; grants no target or input authority",
    }
