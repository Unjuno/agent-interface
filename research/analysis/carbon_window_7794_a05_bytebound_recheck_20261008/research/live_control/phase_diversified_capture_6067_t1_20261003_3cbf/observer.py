"""Capture-only policy; receives offsets/window/epoch, never fixture truth."""
import argparse
import base64
import hashlib
import json
import os
import struct
from pathlib import Path

from common import await_file, until, write
from policy import capture_slots, decode
from x11 import X11


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--display", required=True)
    ap.add_argument("--window", type=int, required=True)
    ap.add_argument("--offsets", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--epoch-file", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    x = X11(a.display)
    frames = []
    journal = (out / "frames.jsonl").open("x")
    try:
        initial = x.keymap()
        write(out / "observer-ready.json", {"pid": os.getpid(), "initial_keymap": initial})
        epoch = await_file(a.epoch_file)["epoch_ns"]
        for index, due_ms in enumerate(capture_slots(json.loads(a.offsets))):
            due = epoch + due_ms * 1_000_000
            until(due)
            start, returned, extracted, pixels = x.capture(a.window)
            raw = struct.pack("<1024I", *pixels)
            frames.append({"index": index, "due_ns": due, "start_ns": start,
                           "native_return_ns": returned, "extracted_ns": extracted,
                           "pixel_sha256": hashlib.sha256(raw).hexdigest(),
                           "pixels_b64": base64.b64encode(raw).decode(), "decoded": decode(pixels)})
            journal.write(json.dumps(frames[-1], sort_keys=True) + "\n")
            journal.flush()
        write(out / "capture.json", {"pid": os.getpid(), "window": a.window,
                                     "epoch_ns": epoch, "frames": frames,
                                     "initial_keymap": initial, "final_keymap": x.keymap()})
    finally:
        journal.close()
        x.close()


if __name__ == "__main__":
    main()
