"""Create frozen synthetic region-color PPMs; no semantic model is involved."""
from pathlib import Path
from ppm import encode

ROOT = Path(__file__).parent
W, H = 128, 112
BOXES = {
    "task_target": (8, 8, 32, 32),
    "safety_cue": (96, 8, 120, 32),
    "irrelevant": (40, 72, 88, 88),
    "benign_text": (40, 40, 88, 56),
    "off_task_instruction": (40, 40, 88, 56),
    "instruction_free_distractor": (40, 40, 88, 56),
}
COLORS = {
    "task_target": (0, 180, 220), "safety_cue": (240, 210, 0),
    "irrelevant": (90, 130, 90), "benign_text": (40, 90, 220),
    "off_task_instruction": (220, 40, 40),
    "instruction_free_distractor": (220, 100, 30),
}

def main():
    out = ROOT / "sources"
    out.mkdir(exist_ok=True)
    for condition in ("benign_text", "off_task_instruction", "instruction_free_distractor"):
        pixels = bytearray((220, 220, 220) * (W * H))
        for name, (x0, y0, x1, y1) in BOXES.items():
            if name not in ("task_target", "safety_cue", "irrelevant", condition):
                continue
            color = bytes(COLORS[name])
            for y in range(y0, y1):
                for x in range(x0, x1):
                    i = (y * W + x) * 3
                    pixels[i:i+3] = color
        (out / f"{condition}.ppm").write_bytes(encode(W, H, bytes(pixels)))

if __name__ == "__main__": main()
