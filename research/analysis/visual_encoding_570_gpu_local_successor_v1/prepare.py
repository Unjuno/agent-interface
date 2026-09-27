from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH, HEIGHT = 1280, 800
PROMPT = (
    "Inspect this synthetic application panel. Find the single blue Apply button. "
    "Return only JSON matching the supplied schema. Coordinates are pixel edges "
    "[left, top, right, bottom] in the 1280x800 image. If there is no Apply button, "
    "return present=false and box=null. Do not guess from other button labels."
)
POSITIVE_SEEDS = [311, 713, 911, 1729, 2027, 4099]
ABSENT_SEEDS = [6151, 8191]
CONSTRUCTION_SEED = 99017
SLOTS = [
    (105, 238, 435, 355), (475, 238, 805, 355), (845, 238, 1175, 355),
    (105, 442, 435, 559), (475, 442, 805, 559), (845, 442, 1175, 559),
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def draw_panel(seed: int, present: bool, font_path: Path, out: Path, fixed_slot: int | None = None) -> dict:
    rng = random.Random(seed)
    img = Image.new("RGB", (WIDTH, HEIGHT), "#f2f5f9")
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(str(font_path), 29)
    header = ImageFont.truetype(str(font_path), 39)
    small = ImageFont.truetype(str(font_path), 22)
    d.rounded_rectangle((40, 35, 1240, 765), radius=24, fill="white", outline="#ccd4df", width=3)
    d.rectangle((43, 38, 1237, 126), fill="#24364b")
    d.text((82, 58), "APPLICATION SETTINGS", font=header, fill="white")
    d.text((82, 157), "Review the available actions", font=small, fill="#526273")
    labels = ["Save", "Cancel", "Reset", "Close", "Help", "More"]
    if present:
        labels[rng.randrange(len(labels))] = "Apply"
    else:
        labels[0] = "Save"
    rng.shuffle(labels)
    slot_order = list(range(6))
    rng.shuffle(slot_order)
    if fixed_slot is not None:
        # Keep the requested off-center target in the lower-right slot.
        target_index = labels.index("Apply") if present else None
        if target_index is not None:
            labels[target_index], labels[slot_order.index(fixed_slot)] = labels[slot_order.index(fixed_slot)], labels[target_index]
    target_box = None
    records = []
    for label, slot_index in zip(labels, slot_order):
        x1, y1, x2, y2 = SLOTS[slot_index]
        is_target = label == "Apply"
        fill = "#2367c9" if is_target else "#e9eef5"
        ink = "white" if is_target else "#304154"
        d.rounded_rectangle((x1, y1, x2, y2), radius=18, fill=fill, outline="#8796a8", width=2)
        bbox = d.textbbox((0, 0), label, font=font)
        tx = x1 + ((x2 - x1) - (bbox[2] - bbox[0])) // 2
        ty = y1 + ((y2 - y1) - (bbox[3] - bbox[1])) // 2 - bbox[1]
        d.text((tx, ty), label, font=font, fill=ink)
        records.append({"label": label, "box": [x1, y1, x2, y2]})
        if is_target:
            target_box = [x1, y1, x2, y2]
    d.text((82, 694), "Changes are not saved until you choose an action.", font=small, fill="#647386")
    img.save(out, format="PNG", optimize=False)
    return {
        "seed": seed,
        "present": present,
        "target_box": target_box,
        "buttons": records,
        "image_path": out.name,
        "image_sha256": sha256(out.read_bytes()),
        "width": WIDTH,
        "height": HEIGHT,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--font", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    if not args.font.is_file():
        raise SystemExit("font file missing")
    args.out.mkdir(parents=True, exist_ok=False)
    cases = []
    for i, seed in enumerate(POSITIVE_SEEDS, 1):
        cases.append({"case_id": f"positive-{i:02d}", **draw_panel(seed, True, args.font, args.out / f"positive-{i:02d}.png")})
    for i, seed in enumerate(ABSENT_SEEDS, 1):
        cases.append({"case_id": f"absent-{i:02d}", **draw_panel(seed, False, args.font, args.out / f"absent-{i:02d}.png")})
    construction = {"case_id": "construction-offcenter", **draw_panel(CONSTRUCTION_SEED, True, args.font, args.out / "construction-offcenter.png", fixed_slot=5)}
    if construction["target_box"][0] < WIDTH * 0.55 or construction["target_box"][1] < HEIGHT * 0.45:
        raise SystemExit("construction target is not off-center")
    manifest = {
        "schema": "visual-encoding-570-local-r4-inputs-v1",
        "allocation": "visual-ruler-qwen25vl-570-r4-local-20260927-01",
        "source_sha256": json.loads((Path(__file__).with_name("FREEZE.json")).read_text(encoding="utf-8"))["source_sha256"],
        "ollama_image_id": "sha256:8262851b2846b87c649eddf3e76beb270c52f4d1bc94559f47efde16b0841551",
        "helper_image_id": "sha256:570ad778e44baf0bd094241515ed6cbbc7ce154321a7d76f295c42f2d5799261",
        "model": "qwen2.5vl:3b",
        "model_digest": "fb90415cde1ef08aa669ae74b082d49b158729b6db1ab183c941417d507e71a1",
        "model_layer_sha256": "e9758e589d443f653821b7be9bb9092c1bf7434522b70ec6e83591b1320fdb4d",
        "model_layer_bytes": 3200614720,
        "prompt": PROMPT,
        "prompt_sha256": sha256(PROMPT.encode()),
        "font_sha256": sha256(args.font.read_bytes()),
        "formal_cases": cases,
        "construction_case": construction,
        "formal_seeds": POSITIVE_SEEDS + ABSENT_SEEDS,
        "no_network_or_provider": True,
    }
    (args.out / "PREFORMAL.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"formal_cases": len(cases), "construction": construction["image_sha256"], "manifest_sha256": sha256((args.out / "PREFORMAL.json").read_bytes())}))


if __name__ == "__main__":
    main()

