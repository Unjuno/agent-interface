#!/usr/bin/env python3
"""Deterministically build the Issue #7387 synthetic cue-deck package."""
import argparse
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
BG = (240, 240, 240)
INKS = {
    "red_square": (220, 30, 30),
    "blue_disk": (20, 70, 220),
    "green_triangle": (20, 170, 60),
    "purple_cross": (160, 30, 180),
}


def ppm(cue=None, width=32, height=32):
    pixels = [BG] * (width * height)
    if cue is not None:
        color = INKS[cue]
        for y in range(8, 24):
            for x in range(8, 24):
                dx, dy = x - 16, y - 16
                if cue == "red_square":
                    inside = True
                elif cue == "blue_disk":
                    inside = dx * dx + dy * dy <= 56
                elif cue == "green_triangle":
                    inside = 8 <= y <= 23 and abs(dx) <= (y - 7) // 2
                else:
                    inside = (abs(dx) <= 2 and abs(dy) <= 8) or (abs(dy) <= 2 and abs(dx) <= 8)
                if inside:
                    pixels[y * width + x] = color
    return f"P6\n{width} {height}\n255\n".encode() + bytes(c for p in pixels for c in p)


def opaque_id(text):
    return hashlib.sha256(text.encode()).hexdigest()[:24]


def build(outdir):
    design = json.loads((ROOT / "design.json").read_text(encoding="utf-8"))
    outdir.mkdir(parents=True, exist_ok=False)
    image_dir = outdir / "images"
    image_dir.mkdir()
    presentations = []
    oracle_rows = []
    frame_count = design["frame_count"]
    for lag in design["lags"]:
        for t2 in design["t2_positions"]:
            t1 = t2 - lag
            if t1 < 0 or t1 >= t2:
                raise ValueError("invalid lag/position")
            for first, second in design["ordered_pairs"]:
                token = opaque_id(f"7387-t0|{lag}|{t2}|{first}|{second}")
                sequence = [None] * frame_count
                sequence[t1] = first
                sequence[t2] = second
                paths = []
                for index, cue in enumerate(sequence):
                    image = ppm(cue, design["width"], design["height"])
                    name = opaque_id(f"{token}|{index}") + ".ppm"
                    (image_dir / name).write_bytes(image)
                    paths.append("images/" + name)
                oracle_rows.append({"token": token, "lag": lag, "t1": t1, "t2": t2,
                                    "cue1": first, "cue2": second, "frames": paths})
                for arm in design["arms"]:
                    prompt = ("Identify both changed symbols and their source frame indices." if arm == "DUAL_REQUIRED"
                              else "Identify only the second changed symbol and its source frame index.")
                    presentations.append({"token": token, "arm": arm, "prompt": prompt,
                                          "source_indices": list(range(frame_count)), "frames": paths})
    isolated = []
    for cue in design["cues"]:
        for pos in design["isolated_positions"]:
            token = opaque_id(f"7387-t0|isolated|{cue}|{pos}")
            frames = [None] * frame_count
            frames[pos] = cue
            paths = []
            for index, event in enumerate(frames):
                image = ppm(event, design["width"], design["height"])
                name = opaque_id(f"{token}|{index}") + ".ppm"
                (image_dir / name).write_bytes(image)
                paths.append("images/" + name)
            isolated.append({"token": token, "position": pos, "prompt": "Identify the one changed symbol and its source frame index.",
                             "source_indices": list(range(frame_count)), "frames": paths})
    (outdir / "presentations.jsonl").write_text("".join(json.dumps(x, sort_keys=True) + "\n" for x in presentations), encoding="utf-8")
    (outdir / "isolated.jsonl").write_text("".join(json.dumps(x, sort_keys=True) + "\n" for x in isolated), encoding="utf-8")
    (outdir / "oracle.json").write_text(json.dumps({"schema": design["schema"], "rows": oracle_rows}, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    files = sorted(p for p in outdir.rglob("*") if p.is_file() and p.name != "SHA256SUMS")
    sums = "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(outdir).as_posix()}\n" for p in files)
    (outdir / "SHA256SUMS").write_text(sums, encoding="ascii")
    print(json.dumps({"presentation_rows": len(presentations), "matched_trials": len(oracle_rows),
                      "isolated_controls": len(isolated), "image_files": sum(1 for p in image_dir.iterdir()),
                      "sha256sums_sha256": hashlib.sha256(sums.encode()).hexdigest()}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    build(pathlib.Path(args.out))


if __name__ == "__main__":
    main()
