"""Build a bounded visual sheet for one verified Mindustry world receipt."""
import hashlib
from pathlib import Path

from PIL import Image, ImageDraw


def build(readiness, runtime_dir, output):
    if readiness.get("status") != "READY" or len(readiness.get("receipts", [])) != 1:
        raise ValueError("one ready world receipt required")
    receipt = readiness["receipts"][0]; evidence = receipt["evidence"]
    runtime_dir = Path(runtime_dir)
    sequence = receipt["dwell_sequences"][-1]
    source = runtime_dir / receipt["last_image"]
    with Image.open(source) as opened:
        crop = opened.convert("RGB").crop(tuple(evidence["box"]))
    if hashlib.sha256(crop.tobytes()).hexdigest() != evidence["last_pixels_sha256"]:
        raise ValueError("world evidence crop digest mismatch")
    scale = min(3, 360 // crop.width, 240 // crop.height)
    if scale < 1: raise ValueError("world receipt exceeds presentation bounds")
    shown = crop.resize((crop.width * scale, crop.height * scale), Image.Resampling.NEAREST)
    canvas = Image.new("RGB", (640, max(120, shown.height + 34)), "white")
    draw = ImageDraw.Draw(canvas)
    point = receipt["point"]
    draw.text((8, 6), f"RECEIPT 1  POINT [{point[0]},{point[1]}]  FRAMES {len(receipt['dwell_sequences'])}", fill="black")
    draw.text((8, 20), "stable animated placement-preview mask; observation evidence only", fill="black")
    canvas.paste(shown, (8, 34)); canvas.save(output)
    return {"size": list(canvas.size), "scale": scale, "crop_size": list(crop.size),
            "source_sequence": sequence, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "presentation_sha256": hashlib.sha256(canvas.tobytes()).hexdigest()}
