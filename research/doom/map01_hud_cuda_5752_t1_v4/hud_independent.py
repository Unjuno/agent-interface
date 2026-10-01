#!/usr/bin/env python3
"""Independent retained-frame HUD reader for #503.

This does not import the project's retained typed HUD readers and never uses retained
health/ammo values to choose its measured result. Typed values are only a later
cross-check of this pixel/WAD reconstruction.
"""
from __future__ import annotations
import hashlib, struct
from pathlib import Path
from PIL import Image

WAD_SHA256 = "a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b"
ANCHORS = {"ammo": (10, 411), "health": (102, 411)}
CLIENT_SIZE = (640, 480)
GLYPH_SIZE = (26, 38)
SLOTS = 3
MIN_SCORE = 0.80
MIN_MARGIN = 0.05

def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def locate_wad() -> Path:
    import vizdoom
    roots = [Path(vizdoom.__file__).resolve().parent, Path(vizdoom.__file__).resolve().parent.parent]
    matches = []
    for root in roots:
        matches.extend(root.rglob("freedoom2.wad"))
    unique, seen = [], set()
    for path in matches:
        rp = path.resolve()
        if rp not in seen:
            seen.add(rp); unique.append(rp)
    good = [p for p in unique if sha256(p) == WAD_SHA256]
    if len(good) != 1:
        raise RuntimeError(f"expected exactly one hash-bound freedoom2.wad, got {[(str(p), sha256(p)) for p in unique]}")
    return good[0]

def read_lumps(path: Path):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != WAD_SHA256:
        raise ValueError("WAD hash mismatch")
    if len(raw) < 12:
        raise ValueError("short WAD")
    magic, count, directory = struct.unpack_from("<4sII", raw, 0)
    if magic not in (b"IWAD", b"PWAD") or directory + 16 * count > len(raw):
        raise ValueError("invalid WAD header/directory")
    out = {}
    for i in range(count):
        off, size, name = struct.unpack_from("<II8s", raw, directory + 16*i)
        if off + size > len(raw):
            raise ValueError("invalid WAD lump bounds")
        out[name.rstrip(b"\0").decode("ascii")] = raw[off:off+size]
    return out

def render_patch(blob: bytes, palette: bytes) -> Image.Image:
    if len(blob) < 8:
        raise ValueError("short patch")
    width, height, _, _ = struct.unpack_from("<hhhh", blob, 0)
    if not (1 <= width <= 512 and 1 <= height <= 512 and 8 + 4*width <= len(blob)):
        raise ValueError("invalid patch geometry")
    rgba = bytearray(width * height * 4)
    for x in range(width):
        cursor = struct.unpack_from("<I", blob, 8 + 4*x)[0]
        guard = 0
        while True:
            if cursor >= len(blob):
                raise ValueError("patch column out of range")
            top = blob[cursor]
            if top == 255:
                break
            if cursor + 4 > len(blob):
                raise ValueError("short patch post")
            length = blob[cursor+1]
            start, end = cursor + 3, cursor + 3 + length
            if end + 1 > len(blob) or top + length > height:
                raise ValueError("bad patch post")
            for j, idx in enumerate(blob[start:end]):
                y = top + j
                dst = 4 * (y * width + x)
                src = 3 * idx
                rgba[dst:dst+3] = palette[src:src+3]
                rgba[dst+3] = 255
            cursor = end + 1
            guard += 1
            if guard > height:
                raise ValueError("excess patch posts")
    return Image.frombytes("RGBA", (width, height), bytes(rgba))

class IndependentHudReader:
    def __init__(self, wad_path: Path):
        lumps = read_lumps(wad_path)
        palette = lumps.get("PLAYPAL", b"")[:768]
        if len(palette) != 768:
            raise ValueError("PLAYPAL missing")
        self.templates = []
        for digit in range(10):
            name = f"STTNUM{digit}"
            if name not in lumps:
                raise ValueError(f"missing {name}")
            patch = render_patch(lumps[name], palette).resize(GLYPH_SIZE, Image.Resampling.NEAREST)
            px = patch.load(); foreground = []
            for y in range(GLYPH_SIZE[1]):
                for x in range(GLYPH_SIZE[0]):
                    if px[x, y][3]:
                        foreground.append((x, y, px[x, y][:3]))
            self.templates.append(foreground)

    def read_signal(self, png: Path, binding: dict, signal: str) -> dict:
        if signal not in ANCHORS:
            raise ValueError(signal)
        geometry = binding.get("geometry") if isinstance(binding, dict) else None
        if not isinstance(geometry, list) or len(geometry) != 4 or tuple(geometry[2:]) != CLIENT_SIZE:
            return {"status":"unknown", "reason":"unsupported_geometry", "value":None}
        left = geometry[0] + ANCHORS[signal][0]
        top = geometry[1] + ANCHORS[signal][1]
        with Image.open(png) as opened:
            frame = opened.convert("RGB")
            if left < 0 or top < 0 or left + SLOTS*GLYPH_SIZE[0] > frame.width or top + GLYPH_SIZE[1] > frame.height:
                return {"status":"unknown", "reason":"outside_frame", "value":None}
            digits, details = [], []
            for slot in range(SLOTS):
                sx = left + slot * GLYPH_SIZE[0]
                scores = []
                for foreground in self.templates:
                    if not foreground:
                        scores.append(0.0); continue
                    matches = sum(frame.getpixel((sx+x, top+y)) == rgb for x, y, rgb in foreground)
                    scores.append(matches / len(foreground))
                order = sorted(range(10), key=lambda d: scores[d], reverse=True)
                best, second = order[:2]
                if scores[best] < MIN_SCORE:
                    digit = None
                elif scores[best] - scores[second] < MIN_MARGIN:
                    return {"status":"unknown", "reason":"ambiguous_digit", "value":None, "detail":{"slot":slot,"scores":scores}}
                else:
                    digit = best
                digits.append(digit)
                details.append({"slot":slot,"digit":digit,"best_digit":best,"best_score":scores[best],"second_score":scores[second]})
        first = next((i for i,d in enumerate(digits) if d is not None), None)
        if first is None or any(d is None for d in digits[first:]) or any(d is not None for d in digits[:first]):
            return {"status":"unknown", "reason":"invalid_right_aligned_number", "value":None, "slots":details}
        return {"status":"observed", "value":int("".join(str(d) for d in digits[first:])), "slots":details}

    def read(self, png: Path, binding: dict) -> dict:
        return {name:self.read_signal(png,binding,name) for name in ("health","ammo")}
