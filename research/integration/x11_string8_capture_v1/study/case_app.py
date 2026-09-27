#!/usr/bin/env python3
"""Cooperative fixture: paint deterministic pixels; never receives an expected decision."""
import argparse
import json
import sys

from Xlib import X
from Xlib.display import Display


def pixels(pattern: str, width: int, height: int) -> list[int]:
    fixed = {
        "all_zero": [0x00000000],
        "ascii_and_utf8": [0x00434241, 0x000080C2],
        "high_non_utf8": [0x00FF0000],
        "mixed": [0x00434241, 0x00FF0000, 0x000080C2, 0x00123456],
        "ordinary_color": [0x00123456, 0x006AAACC, 0x00FEDCBA, 0x00010203],
        "construction_ascii": [0x00434241, 0x000080C2],
        "construction_non_utf8": [0x00FF0011],
    }
    palette = fixed[pattern]
    return [palette[(x + y * width) % len(palette)] for y in range(height) for x in range(width)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=("root", "child"), required=True)
    parser.add_argument("--pattern", required=True)
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    args = parser.parse_args()
    display = Display()
    screen = display.screen()
    root = screen.root
    if args.target == "root":
        drawable = root
    else:
        drawable = root.create_window(16, 16, args.width, args.height, 0, screen.root_depth, X.InputOutput, screen.root_visual, background_pixel=0)
        drawable.map()
        display.sync()
    expected = pixels(args.pattern, args.width, args.height)
    gc = drawable.create_gc(foreground=expected[0])
    for y in range(args.height):
        for x in range(args.width):
            gc.change(foreground=expected[y * args.width + x])
            drawable.fill_rectangle(gc, x, y, 1, 1)
    display.sync()
    gc.free()
    print(json.dumps({"drawable_id": drawable.id, "pixels": expected}, sort_keys=True), flush=True)
    sys.stdin.readline()
    display.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
