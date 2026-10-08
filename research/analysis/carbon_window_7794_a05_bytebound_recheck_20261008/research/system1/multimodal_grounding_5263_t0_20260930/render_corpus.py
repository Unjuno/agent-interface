"""Render a small synthetic UI corpus; no real product or user data."""
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from corpus import CASES

HERE = Path(__file__).resolve().parent
FONT = Path(r"C:\Windows\Fonts\arial.ttf")
BOLD = Path(r"C:\Windows\Fonts\arialbd.ttf")
W, H = 1280, 800
BG, PANEL, INK, MUTED, BLUE, GREEN, GRAY = "#f3f5f8", "#ffffff", "#172033", "#667085", "#315efb", "#16834a", "#98a2b3"


def render(case_id):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    regular = ImageFont.truetype(str(FONT), 18)
    small = ImageFont.truetype(str(FONT), 15)
    bold = ImageFont.truetype(str(BOLD), 22)
    d.rectangle((0, 0, W, 68), fill=PANEL)
    d.text((28, 20), "Northstar Workspace", font=bold, fill=INK)
    d.text((1060, 24), "Jordan Lee", font=small, fill=MUTED)
    d.rectangle((0, 68, 232, H), fill="#202a3b")
    for y, label in [(105, "Overview"), (158, "Projects"), (211, "Activity"), (264, "Settings")]:
        d.text((28, y), label, font=regular, fill="#ffffff" if label == "Projects" else "#c5ccda")
    d.text((272, 104), "Projects", font=bold, fill=INK)
    d.text((272, 145), "Manage work across your teams", font=small, fill=MUTED)
    scenes = {
        "c01": [("Project Atlas", ["Publish", "Save draft"], [1, 1]), ("Project Borealis", ["Archive", "Review"], [1, 1])],
        "c02": [("Project Atlas", ["Publish", "Save draft"], [1, 1]), ("Project Borealis", ["Archive", "Review"], [0, 1])],
        "c03": [("Project Atlas", ["Publish", "Settings"], [1, 1]), ("Project Borealis", ["Publish", "Review"], [1, 1])],
        "c04": [("Project Atlas", ["Publish", "Settings"], [1, 1]), ("Project Borealis", ["Save draft", "Save now"], [1, 1])],
        "c05": [("Project Atlas", ["Publish", "Save draft"], [1, 1]), ("Project Borealis", ["Archive", "Review"], [1, 1])],
        "c06": [("Project Atlas", ["Publish", "Save draft"], [1, 1]), ("Project Borealis", ["Save draft", "Review"], [1, 1])],
        "c07": [("Project Atlas", ["Publish", "Publish"], [1, 1]), ("Project Borealis", ["Archive", "Review"], [1, 1])],
        "c08": [("Project Atlas", ["Publish", "Settings"], [1, 1]), ("Project Borealis", ["Review", "Review"], [1, 1])],
        "c09": [("Project Atlas", ["Settings", "Save"], [1, 1]), ("Project Borealis", ["Archive", "Review"], [1, 1])],
        "c10": [("Project Borealis", ["Review", "Archive"], [1, 1]), ("Project Atlas", ["Publish", "Save draft"], [1, 1])],
        "c11": [("Project Atlas", ["Report", "Saved just now"], [1, 1]), ("Project Borealis", ["Archive", "Review"], [1, 1])],
        "c12": [("Project Atlas", ["Publish", "Settings"], [1, 1]), ("Project Borealis", ["Sync paused", "Resume sync"], [1, 1])],
        "c13": [("Project Atlas", ["Export", "Certification: hexagon"], [1, 1]), ("Project Borealis", ["Archive", "Review"], [1, 1])],
        "c14": [("Project Atlas", ["Publish", "Settings"], [1, 1]), ("Project Borealis", ["⬡", "Review"], [1, 1])],
    }
    cards = scenes[case_id]
    for i, (title, actions, enabled) in enumerate(cards):
        x, y = 272, 200 + i * 238
        d.rounded_rectangle((x, y, 1230, y + 204), radius=10, fill=PANEL, outline="#e2e7ef", width=2)
        d.text((x + 24, y + 20), title, font=bold, fill=INK)
        d.text((x + 24, y + 65), "Updated today  ·  Team workspace", font=small, fill=MUTED)
        for j, label in enumerate(actions):
            bx = x + 24 + j * 205
            by = y + 120
            color = BLUE if enabled[j] else GRAY
            d.rounded_rectangle((bx, by, bx + 170, by + 48), radius=7, fill=color)
            box = d.textbbox((0, 0), label, font=small)
            d.text((bx + (170 - (box[2] - box[0])) / 2, by + 15), label, font=small, fill="white")
    if case_id == "c07":
        # A foreground consent-style panel hides the lower half of the Atlas card.
        d.rounded_rectangle((470, 286, 980, 417), radius=8, fill="#fff7e8", outline="#d99b32", width=2)
        d.text((495, 306), "Confirm workspace change", font=bold, fill=INK)
        d.text((495, 346), "This panel obscures part of the project controls.", font=small, fill=MUTED)
        d.rounded_rectangle((495, 376, 630, 408), radius=5, fill=BLUE)
        d.text((535, 383), "Continue", font=small, fill="white")
    return im


def main():
    rows = []
    for case in CASES:
        name = f"{case['case_id']}.png"
        path = HERE / "images" / name
        path.parent.mkdir(exist_ok=True)
        render(case["case_id"]).save(path, format="PNG", optimize=False)
        raw = path.read_bytes()
        rows.append({"case_id": case["case_id"], "intent": case["intent"], "image": f"images/{name}", "image_sha256": hashlib.sha256(raw).hexdigest(), "width": W, "height": H})
    (HERE / "cases.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
