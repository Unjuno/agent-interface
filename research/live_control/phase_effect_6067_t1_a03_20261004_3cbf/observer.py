"""Read-only source/ID acquisition plus prospective deadline/resource telemetry."""
import argparse
import base64
import hashlib
import json
import os
import struct
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import await_file, write
from policy import capture_slots, decode
from x11 import X11
from timing import paced_wait, snapshot

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--display", required=True)
    ap.add_argument("--window", type=int, required=True)
    ap.add_argument("--offsets", required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--epoch-file", type=Path, required=True)
    a = ap.parse_args()
    x = X11(a.display)
    frames = []
    with (a.out / "frames.jsonl").open("x") as journal, (a.out / "waits.jsonl").open("x") as waits:
        try:
            initial = x.keymap()
            write(a.out / "observer-ready.json", {"pid": os.getpid(), "initial_keymap": initial})
            epoch = await_file(a.epoch_file)["epoch_ns"]
            epoch_read_ns = time.monotonic_ns()
            for i, ms in enumerate(capture_slots(json.loads(a.offsets))):
                due = epoch + ms * 1_000_000
                pre = snapshot()
                wait = paced_wait(due)
                post = snapshot()
                trace = {"index": i, "due_ns": due, "pre": pre, "wait": wait, "post": post}
                waits.write(json.dumps(trace, sort_keys=True) + "\n")
                waits.flush()
                start, returned, extracted, pixels = x.capture(a.window)
                raw = struct.pack("<1024I", *pixels)
                frame = {**trace, "start_ns": start, "native_return_ns": returned,
                         "extracted_ns": extracted, "pixel_sha256": hashlib.sha256(raw).hexdigest(),
                         "pixels_b64": base64.b64encode(raw).decode(), "decoded": decode(pixels)}
                frames.append(frame)
                journal.write(json.dumps(frame, sort_keys=True) + "\n")
                journal.flush()
            write(a.out / "capture.json", {"pid": os.getpid(), "window": a.window, "epoch_ns": epoch,
                "epoch_read_ns": epoch_read_ns, "frames": frames,
                "initial_keymap": initial, "final_keymap": x.keymap(),
                "note": "instrumented pacing variant; post-wait snapshot/trace flush overhead measured, not original A01"})
        finally:
            x.close()

if __name__ == "__main__":
    main()
