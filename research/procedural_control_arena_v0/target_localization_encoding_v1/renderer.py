from __future__ import annotations

import json
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from engine import HEIGHT, PLAY_BOTTOM, PLAY_TOP, WIDTH, BenchmarkSession, EpisodeSpec, StageSpec, generate_episode


SERIES = {"blue": "#4c78a8", "red": "#e45756", "green": "#54a24b", "yellow": "#eeca3b",
          "purple": "#b279a2", "orange": "#f58518"}


FONT = {
    "0": (7, 5, 7, 7, 5, 7, 7), "1": (2, 6, 2, 2, 2, 2, 7),
    "2": (7, 1, 1, 7, 4, 4, 7), "3": (7, 1, 1, 7, 1, 1, 7),
    "4": (5, 5, 5, 7, 1, 1, 1), "5": (7, 4, 4, 7, 1, 1, 7),
    "6": (7, 4, 4, 7, 5, 5, 7), "7": (7, 1, 1, 2, 2, 2, 2),
    "8": (7, 5, 5, 7, 5, 5, 7), "9": (7, 5, 5, 7, 1, 1, 7),
}


@dataclass
class Raster:
    width: int = WIDTH
    height: int = HEIGHT

    def __post_init__(self) -> None:
        self.pixels = bytearray((17, 19, 24)) * (self.width * self.height)

    def put(self, x: int, y: int, color: tuple[int, int, int]) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            offset = (y * self.width + x) * 3
            self.pixels[offset:offset + 3] = bytes(color)

    def line(self, x0: int, y0: int, x1: int, y1: int, color: tuple[int, int, int]) -> None:
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        error = dx + dy
        while True:
            self.put(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            twice = 2 * error
            if twice >= dy:
                error += dy
                x0 += sx
            if twice <= dx:
                error += dx
                y0 += sy

    def rect(self, x0: int, y0: int, x1: int, y1: int, color: tuple[int, int, int], *, fill: bool) -> None:
        if fill:
            for y in range(y0, y1 + 1):
                self.line(x0, y, x1, y, color)
        else:
            self.line(x0, y0, x1, y0, color)
            self.line(x1, y0, x1, y1, color)
            self.line(x1, y1, x0, y1, color)
            self.line(x0, y1, x0, y0, color)

    def circle(self, cx: int, cy: int, radius: int, color: tuple[int, int, int], *, fill: bool) -> None:
        rr = radius * radius
        for y in range(cy - radius, cy + radius + 1):
            for x in range(cx - radius, cx + radius + 1):
                d = (x - cx) ** 2 + (y - cy) ** 2
                if d <= rr and (fill or d >= (radius - 2) ** 2):
                    self.put(x, y, color)

    def polygon(self, points: list[tuple[int, int]], color: tuple[int, int, int], *, fill: bool) -> None:
        if not fill:
            for a, b in zip(points, points[1:] + points[:1]):
                self.line(*a, *b, color)
            return
        ymin = min(y for _, y in points)
        ymax = max(y for _, y in points)
        for y in range(ymin, ymax + 1):
            xs = []
            for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1]):
                if y0 == y1 or not (min(y0, y1) <= y < max(y0, y1)):
                    continue
                xs.append(round(x0 + (y - y0) * (x1 - x0) / (y1 - y0)))
            xs.sort()
            for left, right in zip(xs[0::2], xs[1::2]):
                self.line(left, y, right, y, color)

    def text(self, x: int, y: int, text: str, color: tuple[int, int, int]) -> None:
        for char in text:
            rows = FONT.get(char)
            if rows:
                for row, bits in enumerate(rows):
                    for col in range(3):
                        if bits & (1 << (2 - col)):
                            self.put(x + col, y + row, color)
            x += 5

    def png(self) -> bytes:
        raw = b"".join(b"\0" + self.pixels[y * self.width * 3:(y + 1) * self.width * 3] for y in range(self.height))
        def chunk(kind: bytes, payload: bytes) -> bytes:
            body = kind + payload
            return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body) & 0xffffffff)
        return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">2I5B", self.width, self.height, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def _stage(seed: int, difficulty: float) -> tuple[EpisodeSpec, BenchmarkSession]:
    full = generate_episode(seed, difficulty)
    target = next(stage for stage in full.stages if stage.kind == "target")
    spec = EpisodeSpec(full.schema, full.seed, full.difficulty, (StageSpec(target.kind, target.payload),))
    return spec, BenchmarkSession(spec)


def render_base(seed: int, difficulty: float) -> tuple[bytes, dict[str, Any]]:
    _, session = _stage(seed, difficulty)
    raster = Raster()
    target = session._object_by_id(session.stage.payload["target_id"])
    colors = {name: tuple(int(SERIES[name][i:i + 2], 16) for i in (1, 3, 5)) for name in SERIES}
    # Arena v0 playfield boundary and object shapes; the task instruction is identical text outside the image.
    raster.line(0, PLAY_TOP, WIDTH - 1, PLAY_TOP, (66, 72, 84))
    raster.line(0, PLAY_BOTTOM, WIDTH - 1, PLAY_BOTTOM, (66, 72, 84))
    for obj in session.objects:
        x, y, r = round(obj.x), round(obj.y), round(obj.radius)
        color = colors[obj.color]
        if obj.shape == "circle":
            raster.circle(x, y, r, color, fill=True)
            raster.circle(x, y, r, (242, 242, 242), fill=False)
        elif obj.shape == "square":
            raster.rect(x-r, y-r, x+r, y+r, color, fill=True)
            raster.rect(x-r, y-r, x+r, y+r, (242, 242, 242), fill=False)
        elif obj.shape == "triangle":
            points = [(x, y-r), (x-r, y+r), (x+r, y+r)]
            raster.polygon(points, color, fill=True)
            raster.polygon(points, (242, 242, 242), fill=False)
        elif obj.shape == "diamond":
            points = [(x, y-r), (x-r, y), (x, y+r), (x+r, y)]
            raster.polygon(points, color, fill=True)
            raster.polygon(points, (242, 242, 242), fill=False)
    truth = {
        "seed": seed,
        "difficulty": difficulty,
        "instruction": session.instruction(),
        "target": {"color": target.color, "shape": target.shape, "center_x": target.x, "center_y": target.y, "radius": target.radius},
        "objects": [{"color": obj.color, "shape": obj.shape, "center_x": obj.x, "center_y": obj.y, "radius": obj.radius} for obj in session.objects],
    }
    return raster.png(), truth


def render_pair(seed: int, difficulty: float) -> tuple[bytes, bytes, dict[str, Any]]:
    raw, truth = render_base(seed, difficulty)
    _, session = _stage(seed, difficulty)
    raster = Raster()
    colors = {name: tuple(int(SERIES[name][i:i + 2], 16) for i in (1, 3, 5)) for name in SERIES}
    raster.line(0, PLAY_TOP, WIDTH - 1, PLAY_TOP, (66, 72, 84))
    raster.line(0, PLAY_BOTTOM, WIDTH - 1, PLAY_BOTTOM, (66, 72, 84))
    for obj in session.objects:
        x, y, r = round(obj.x), round(obj.y), round(obj.radius)
        color = colors[obj.color]
        if obj.shape == "circle":
            raster.circle(x, y, r, color, fill=True)
            raster.circle(x, y, r, (242, 242, 242), fill=False)
        elif obj.shape == "square":
            raster.rect(x-r, y-r, x+r, y+r, color, fill=True)
            raster.rect(x-r, y-r, x+r, y+r, (242, 242, 242), fill=False)
        elif obj.shape == "triangle":
            points = [(x, y-r), (x-r, y+r), (x+r, y+r)]
            raster.polygon(points, color, fill=True)
            raster.polygon(points, (242, 242, 242), fill=False)
        elif obj.shape == "diamond":
            points = [(x, y-r), (x-r, y), (x, y+r), (x+r, y)]
            raster.polygon(points, color, fill=True)
            raster.polygon(points, (242, 242, 242), fill=False)
    # GRID80 is a foreground overlay on the same scene; geometry and
    # source-coordinate mapping remain unchanged.
    for x in range(0, WIDTH, 80):
        raster.line(x, PLAY_TOP, x, PLAY_BOTTOM, (49, 54, 63))
        raster.text(x + 2, PLAY_TOP + 3, str(x), (120, 128, 141))
    for y in range(PLAY_TOP, PLAY_BOTTOM + 1, 80):
        raster.line(0, y, WIDTH - 1, y, (49, 54, 63))
        raster.text(2, y + 3, str(y), (120, 128, 141))
    return raw, raster.png(), truth


def save_pair(directory: Path, seed: int, difficulty: float) -> dict[str, Any]:
    directory.mkdir(parents=True, exist_ok=True)
    raw, grid, truth = render_pair(seed, difficulty)
    (directory / "raw.png").write_bytes(raw)
    (directory / "grid80.png").write_bytes(grid)
    (directory / "truth.json").write_text(json.dumps(truth, sort_keys=True) + "\n", encoding="utf-8")
    return truth
