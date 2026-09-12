#!/usr/bin/env python3
"""C0 vs C1 control-serialization benchmark.

This benchmark is intentionally model-free. It compares two encodings of the
same semantic operation list:

C0: compact JSON action list
C1: compact fixed-grammar text IR

It reports serialization bytes and C1 parse time. Bytes are a serialization
proxy, not model tokens.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import statistics
import time
from pathlib import Path
from typing import Any

KEYS = ["A", "C", "G", "X", "ENTER", "ESC", "TAB", "CTRL", "SHIFT", "ALT"]
BUTTONS = ["L", "R"]
WORDS = ["hello", "save", "0.3", "draft", "node", "layer", "frame"]
WINDOWS = ["editor", "canvas", "terminal", "browser"]
ASSERTS = ["changed", "focused", "dialog_closed", "selection_exists"]


def _split(program: str) -> list[str]:
    out: list[str] = []
    buf: list[str] = []
    quoted = False
    escaped = False
    for ch in program:
        if escaped:
            buf.append(ch)
            escaped = False
            continue
        if quoted and ch == "\\":
            buf.append(ch)
            escaped = True
            continue
        if ch == '"':
            quoted = not quoted
            buf.append(ch)
            continue
        if ch == ";" and not quoted:
            token = "".join(buf)
            if token:
                out.append(token)
            buf.clear()
            continue
        buf.append(ch)
    if quoted:
        raise ValueError("unterminated string")
    token = "".join(buf)
    if token:
        out.append(token)
    return out


def encode_c1(ops: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for op in ops:
        t = op["type"]
        if t == "key":
            parts.append("k:" + "+".join(op["keys"]))
        elif t == "key_down":
            parts.append("kd:" + op["key"])
        elif t == "key_up":
            parts.append("ku:" + op["key"])
        elif t == "text":
            parts.append("t:" + json.dumps(op["text"], ensure_ascii=False, separators=(",", ":")))
        elif t == "move_abs":
            parts.append(f"ma:{op['x']},{op['y']}")
        elif t == "move_rel":
            parts.append(f"mr:{op['dx']},{op['dy']}")
        elif t == "button_down":
            parts.append("bd:" + op["button"])
        elif t == "button_up":
            parts.append("bu:" + op["button"])
        elif t == "click":
            parts.append(f"c:{op['x']},{op['y']},{op['button']}")
        elif t == "scroll":
            parts.append(f"s:{op['dx']},{op['dy']}")
        elif t == "focus":
            parts.append("f:" + json.dumps(op["target"], ensure_ascii=False, separators=(",", ":")))
        elif t == "wait_update":
            parts.append("w")
        elif t == "observe":
            parts.append(f"o:{op['x']},{op['y']},{op['w']},{op['h']}")
        elif t == "assert":
            parts.append("a:" + json.dumps(op["predicate"], ensure_ascii=False, separators=(",", ":")))
        else:
            raise ValueError(f"unsupported op: {t}")
    return ";".join(parts)


def decode_c1(program: str) -> list[dict[str, Any]]:
    ops: list[dict[str, Any]] = []
    for token in _split(program):
        if token == "w":
            ops.append({"type": "wait_update"})
            continue
        code, payload = token.split(":", 1)
        if code == "k":
            ops.append({"type": "key", "keys": payload.split("+")})
        elif code == "kd":
            ops.append({"type": "key_down", "key": payload})
        elif code == "ku":
            ops.append({"type": "key_up", "key": payload})
        elif code == "t":
            ops.append({"type": "text", "text": json.loads(payload)})
        elif code == "ma":
            x, y = map(int, payload.split(","))
            ops.append({"type": "move_abs", "x": x, "y": y})
        elif code == "mr":
            dx, dy = map(int, payload.split(","))
            ops.append({"type": "move_rel", "dx": dx, "dy": dy})
        elif code == "bd":
            ops.append({"type": "button_down", "button": payload})
        elif code == "bu":
            ops.append({"type": "button_up", "button": payload})
        elif code == "c":
            x, y, button = payload.split(",")
            ops.append({"type": "click", "x": int(x), "y": int(y), "button": button})
        elif code == "s":
            dx, dy = map(int, payload.split(","))
            ops.append({"type": "scroll", "dx": dx, "dy": dy})
        elif code == "f":
            ops.append({"type": "focus", "target": json.loads(payload)})
        elif code == "o":
            x, y, w, h = map(int, payload.split(","))
            ops.append({"type": "observe", "x": x, "y": y, "w": w, "h": h})
        elif code == "a":
            ops.append({"type": "assert", "predicate": json.loads(payload)})
        else:
            raise ValueError(f"unknown opcode: {code}")
    return ops


def encode_c0(ops: list[dict[str, Any]]) -> str:
    return json.dumps(ops, ensure_ascii=False, separators=(",", ":"))


def generate_program(rng: random.Random, nominal_ops: int) -> list[dict[str, Any]]:
    ops: list[dict[str, Any]] = []
    held_keys: set[str] = set()
    held_buttons: set[str] = set()

    choices = ["key", "text", "move_abs", "move_rel", "click", "scroll", "focus", "wait", "observe", "assert"]

    while len(ops) < nominal_ops:
        choice = rng.choice(choices)
        remaining = nominal_ops - len(ops)

        if choice == "key" and remaining >= 2 and rng.random() < 0.20:
            key = rng.choice(["CTRL", "SHIFT", "ALT"])
            if key not in held_keys:
                held_keys.add(key)
                ops.append({"type": "key_down", "key": key})
                continue
        if held_keys and rng.random() < 0.12:
            key = rng.choice(sorted(held_keys))
            held_keys.remove(key)
            ops.append({"type": "key_up", "key": key})
            continue
        if choice == "click" and remaining >= 2 and rng.random() < 0.12:
            button = rng.choice(BUTTONS)
            if button not in held_buttons:
                held_buttons.add(button)
                ops.append({"type": "button_down", "button": button})
                continue
        if held_buttons and rng.random() < 0.12:
            button = rng.choice(sorted(held_buttons))
            held_buttons.remove(button)
            ops.append({"type": "button_up", "button": button})
            continue

        if choice == "key":
            keys = [rng.choice(KEYS[:7])]
            if rng.random() < 0.18:
                keys.insert(0, rng.choice(["CTRL", "SHIFT", "ALT"]))
            ops.append({"type": "key", "keys": keys})
        elif choice == "text":
            ops.append({"type": "text", "text": rng.choice(WORDS)})
        elif choice == "move_abs":
            ops.append({"type": "move_abs", "x": rng.randrange(0, 1920), "y": rng.randrange(0, 1080)})
        elif choice == "move_rel":
            ops.append({"type": "move_rel", "dx": rng.randrange(-200, 201), "dy": rng.randrange(-200, 201)})
        elif choice == "click":
            ops.append({"type": "click", "x": rng.randrange(0, 1920), "y": rng.randrange(0, 1080), "button": rng.choice(BUTTONS)})
        elif choice == "scroll":
            ops.append({"type": "scroll", "dx": rng.randrange(-8, 9), "dy": rng.randrange(-8, 9)})
        elif choice == "focus":
            ops.append({"type": "focus", "target": rng.choice(WINDOWS)})
        elif choice == "wait":
            ops.append({"type": "wait_update"})
        elif choice == "observe":
            ops.append({"type": "observe", "x": rng.randrange(0, 1500), "y": rng.randrange(0, 800), "w": rng.randrange(32, 401), "h": rng.randrange(32, 301)})
        elif choice == "assert":
            ops.append({"type": "assert", "predicate": rng.choice(ASSERTS)})

    for key in sorted(held_keys):
        ops.append({"type": "key_up", "key": key})
    for button in sorted(held_buttons):
        ops.append({"type": "button_up", "button": button})
    return ops


def run(seed: int, programs: int, sizes: list[int]) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    rows: list[dict[str, Any]] = []
    for size in sizes:
        samples: list[dict[str, float]] = []
        for _ in range(programs):
            ops = generate_program(rng, size)
            c0 = encode_c0(ops)
            c1 = encode_c1(ops)
            start = time.perf_counter_ns()
            decoded = decode_c1(c1)
            parse_ns = time.perf_counter_ns() - start
            if decoded != ops:
                raise AssertionError("C1 round-trip mismatch")
            samples.append({
                "c0": len(c0.encode("utf-8")),
                "c1": len(c1.encode("utf-8")),
                "parse_us": parse_ns / 1000.0,
                "actual_ops": len(ops),
            })
        rows.append({
            "nominal_ops": size,
            "programs": programs,
            "median_actual_ops": statistics.median(s["actual_ops"] for s in samples),
            "median_c0_bytes": statistics.median(s["c0"] for s in samples),
            "median_c1_bytes": statistics.median(s["c1"] for s in samples),
            "median_reduction_pct": 100.0 * (1.0 - statistics.median(s["c1"] for s in samples) / statistics.median(s["c0"] for s in samples)),
            "median_c1_parse_us": statistics.median(s["parse_us"] for s in samples),
            "roundtrip_failures": 0,
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20260913)
    parser.add_argument("--programs", type=int, default=1000, help="programs per size")
    parser.add_argument("--sizes", default="4,8,16,32,64")
    parser.add_argument("--out", type=Path, default=Path("control_codec_summary.csv"))
    args = parser.parse_args()

    sizes = [int(x) for x in args.sizes.split(",") if x]
    rows = run(args.seed, args.programs, sizes)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    for row in rows:
        print(
            f"ops={row['nominal_ops']:>2} "
            f"C0={row['median_c0_bytes']:>7.1f}B "
            f"C1={row['median_c1_bytes']:>7.1f}B "
            f"reduction={row['median_reduction_pct']:>5.1f}% "
            f"parse={row['median_c1_parse_us']:>7.2f}us"
        )
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
