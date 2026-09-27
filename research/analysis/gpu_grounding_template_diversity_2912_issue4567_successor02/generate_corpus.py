#!/usr/bin/env python3
"""Render a deterministic, explicitly synthetic multi-template form corpus."""
import argparse
import hashlib
import json
import random
from pathlib import Path

import PIL
from PIL import Image, ImageDraw, ImageFont


HERE = Path(__file__).resolve().parent
SPEC_PATH = HERE / "templates.json"
GENERATOR_VERSION = "pil-form-renderer-v1"
RENDER_SCALE = 2
SOURCE_UPSCALE = 2
PALETTES = [
    {"panel":"#ffffff","ink":"#172033","muted":"#64748b","field":"#ffffff","border":"#94a3b8"},
    {"panel":"#fffdf7","ink":"#1f2937","muted":"#6b7280","field":"#ffffff","border":"#9ca3af"},
    {"panel":"#f8fafc","ink":"#0f172a","muted":"#475569","field":"#ffffff","border":"#64748b"},
    {"panel":"#fff7ed","ink":"#292524","muted":"#78716c","field":"#ffffff","border":"#a8a29e"},
]
TITLES = ["Create your account", "Contact details", "Sign in to continue", "Profile information", "Join the workspace"]
LABELS = ["Email address", "Work email", "Your email", "Email", "Account email"]
PLACEHOLDERS = ["name@example.test", "you@sample.test", "Enter email", "user@local.test", "email address"]
BUTTONS = ["Continue", "Save details", "Next step", "Submit form", "Create account"]


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def rect(box, dx=0, dy=0):
    x, y, w, h = box
    return [x + dx, y + dy, x + dx + w, y + dy + h]


def point(box, dx=0, dy=0):
    x, y, w, h = box
    # Quantize the visual center to an 8-source-pixel grid so the target is
    # exactly representable by the frozen 160x100 model input.
    source_scale = RENDER_SCALE * SOURCE_UPSCALE
    values = [source_scale * (x + dx + w // 2), source_scale * (y + dy + h // 2)]
    return [((value + 4) // 8) * 8 for value in values]


def render(spec, variant, font):
    rng = random.Random(29120000 + int(spec["id"][1:]) * 1000 + variant)
    dx = rng.choice([-4, -2, 0, 2, 4])
    dy = rng.choice([-2, 0, 2, 4])
    palette = PALETTES[(variant + int(spec["id"][1:])) % len(PALETTES)]
    dark = spec["kind"] == "dark-card"
    if dark:
        palette = {"panel":"#1f2937","ink":"#f9fafb","muted":"#cbd5e1","field":"#111827","border":"#64748b"}

    image = Image.new("RGB", (640, 400), spec["background"])
    draw = ImageDraw.Draw(image)

    def box(values):
        return tuple(value * RENDER_SCALE for value in values)

    def xy(x, y):
        return x * RENDER_SCALE, y * RENDER_SCALE

    decor = spec["decoration"]
    if decor == "topline":
        draw.rectangle(box((0, 0, 319, 7)), fill=spec["accent"])
    elif decor == "split":
        draw.rectangle(box((0, 0, 119, 199)), fill="#e7e5e4")
        draw.text(xy(14, 50), "ACCOUNT", fill="#57534e", font=font)
    elif decor == "left-sidebar":
        draw.rectangle(box((0, 0, 48, 199)), fill=spec["accent"])
        draw.rectangle(box((10, 28, 38, 48)), fill="#ffffff")
        draw.rectangle(box((10, 64, 38, 68)), fill="#ffffff")
    elif decor == "right-sidebar":
        draw.rectangle(box((266, 0, 319, 199)), fill="#e7e5e4")
        draw.rectangle(box((278, 42, 306, 46)), fill=spec["accent"])
    elif decor == "banner":
        draw.rectangle(box((0, 0, 319, 28)), fill=spec["accent"])
        draw.text(xy(16, 8), "MEMBER PORTAL", fill="#ffffff", font=font)
    elif decor == "left-rail":
        draw.rectangle(box((0, 0, 72, 199)), fill="#e2e8f0")
        draw.rectangle(box((12, 40, 56, 46)), fill=spec["accent"])
        draw.rectangle(box((12, 62, 52, 66)), fill="#94a3b8")
    elif decor == "dim-overlay":
        draw.rectangle(box((0, 0, 319, 199)), fill="#64748b")
    elif decor == "bottom-rule":
        draw.rectangle(box((0, 184, 319, 199)), fill="#e7e5e4")
    elif decor == "action-bar":
        draw.rectangle(box((36, 138, 283, 192)), fill="#e2e8f0")
    elif decor == "right-rail":
        draw.rectangle(box((254, 38, 319, 188)), fill="#fbcfe8")

    px1, py1, px2, py2 = rect(spec["panel"], dx, dy)
    draw.rounded_rectangle(box((px1, py1, px2, py2)), radius=8 * RENDER_SCALE,
                           fill=palette["panel"], outline=palette["border"], width=RENDER_SCALE)
    draw.text(xy(px1 + 12, py1 + 10), TITLES[(variant + int(spec["id"][1:])) % len(TITLES)],
              fill=palette["ink"], font=font)

    fx1, fy1, fx2, fy2 = rect(spec["field"], dx, dy)
    draw.text(xy(fx1, fy1 - 11), LABELS[variant % len(LABELS)], fill=palette["muted"], font=font)
    draw.rounded_rectangle(box((fx1, fy1, fx2, fy2)), radius=3 * RENDER_SCALE,
                           fill=palette["field"], outline=palette["border"], width=RENDER_SCALE)
    draw.text(xy(fx1 + 4, fy1 + 5), PLACEHOLDERS[(variant + 2) % len(PLACEHOLDERS)],
              fill=palette["muted"], font=font)

    sx1, sy1, sx2, sy2 = rect(spec["submit"], dx, dy)
    draw.rounded_rectangle(box((sx1, sy1, sx2, sy2)), radius=4 * RENDER_SCALE, fill=spec["accent"])
    button = BUTTONS[(variant + 1) % len(BUTTONS)]
    bbox = draw.textbbox((0, 0), button, font=font)
    tw, th = (bbox[2] - bbox[0]) // RENDER_SCALE, (bbox[3] - bbox[1]) // RENDER_SCALE
    draw.text(xy(sx1 + max(2, (sx2 - sx1 - tw) // 2), sy1 + max(2, (sy2 - sy1 - th) // 2)),
              button, fill="#ffffff", font=font)
    return image, {"field_point": point(spec["field"], dx, dy), "submit_point": point(spec["submit"], dx, dy)}


def build(out_root):
    if PIL.__version__ != "10.4.0":
        raise RuntimeError(f"Pillow 10.4.0 required, found {PIL.__version__}")
    spec_raw = SPEC_PATH.read_bytes()
    spec_doc = json.loads(spec_raw)
    source_specs = spec_doc["families"]
    if len(source_specs) != 12 or sum(row["split"] == "train" for row in source_specs) != 8:
        raise ValueError("frozen template family/split contract mismatch")
    if sum(row["split"] == "heldout" for row in source_specs) != 4:
        raise ValueError("frozen held-out family count mismatch")
    font = ImageFont.load_default(size=18)
    rows = []
    for spec in source_specs:
        source_digest = sha256(canonical(spec))
        for variant in range(spec_doc["variants_per_family"]):
            image, labels = render(spec, variant, font)
            source_image = image.resize((1280, 800), Image.Resampling.NEAREST)
            rel = Path("images") / spec["id"] / f"v{variant:02d}.png"
            dest = out_root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            source_image.save(dest, format="PNG", optimize=False, compress_level=9)
            raw = dest.read_bytes()
            rows.append({"record_id": f"{spec['id']}-v{variant:02d}", "family_id": spec["id"],
                         "split": spec["split"], "variant": variant, "image": rel.as_posix(),
                         "image_sha256": sha256(raw), "template_spec_sha256": source_digest,
                         "field_point": labels["field_point"], "submit_point": labels["submit_point"],
                         "typed_outcome": "synthetic_target_defined"})
    generator_bytes = Path(__file__).read_bytes().replace(b"\r\n", b"\n")
    manifest = {"format": "synthetic-form-grounding-source-manifest-v1",
                "generator": GENERATOR_VERSION, "generator_sha256": sha256(generator_bytes),
                "template_spec_sha256": sha256(canonical(spec_doc)),
                "renderer": {"pillow": "10.4.0", "template_unit_canvas": [320, 200],
                             "logical_canvas": [640, 400], "source_canvas": [1280, 800], "source_scale": 2,
                             "model_input": [160, 100], "font": "Pillow ImageFont.load_default(size=18)",
                             "resample_source": "NEAREST", "resample_model": "BILINEAR"},
                "seed": 2912, "families": [{"family_id": row["id"], "split": row["split"],
                                               "spec_sha256": sha256(canonical(row))}
                                              for row in source_specs],
                "records": rows, "skipped": []}
    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "manifest.json").write_bytes(canonical(manifest))
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=HERE / "corpus")
    args = parser.parse_args()
    manifest = build(args.out.resolve())
    print(json.dumps({"records": len(manifest["records"]),
                      "train_families": sum(row["split"] == "train" for row in manifest["families"]),
                      "heldout_families": sum(row["split"] == "heldout" for row in manifest["families"]),
                      "manifest_sha256": sha256((args.out.resolve() / "manifest.json").read_bytes()),
                      "unique_images": len({row["image_sha256"] for row in manifest["records"]})},
                     sort_keys=True))


if __name__ == "__main__":
    main()
