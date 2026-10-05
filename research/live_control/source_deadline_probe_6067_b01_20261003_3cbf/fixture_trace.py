"""Independent visual producer. Its truth is not an online controller input."""
import argparse
import json
import os
from pathlib import Path

from common import await_file, until, write
from x11 import X11
from timing import paced_wait, snapshot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--display", required=True)
    ap.add_argument("--cell", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    spec = json.loads(Path(a.cell).read_text())
    root = Path(a.out)
    x = X11(a.display)
    w, gc = x.make_window()
    trace = root.joinpath("source.jsonl").open("x")
    events = []
    source_waits = []
    wait_log = root.joinpath('source-waits.jsonl').open('x')
    def traced_wait(due, kind, identity):
        pre = snapshot()
        waited = paced_wait(due)
        post = snapshot()
        return {'kind':kind,'id':identity,'due_ns':due,'pre':pre,'wait':waited,'post':post}
    def record_wait(waited, start, end):
        waited.update(paint_start_ns=start, paint_end_ns=end)
        source_waits.append(waited)
        wait_log.write(json.dumps(waited, sort_keys=True) + '\n')
        wait_log.flush()
    try:
        write(root / "fixture-ready.json", {"pid": os.getpid(), "window": w})
        epoch = await_file(root / "epoch.json")["epoch_ns"]
        if spec["kind"] == "pulse":
            plan = [(i + 1, 120 * i + 10 * spec["phase"] + 2,
                     120 * i + 10 * spec["phase"] + 2 + spec["width_ms"])
                    for i in range(8)]
        elif spec["kind"] == "persistent":
            plan = [(1, -20, 1000)]
        else:
            plan = []
        for identity, onset_ms, clear_ms in plan:
            color = 0xFF0000 if identity % 2 else 0x00FF00
            onset, clear = epoch + onset_ms * 1_000_000, epoch + clear_ms * 1_000_000
            draw_wait = traced_wait(onset, 'draw', identity)
            start, end = x.paint(w, gc, identity, color)
            record_wait(draw_wait, start, end)
            trace.write(json.dumps({"event": "draw", "id": identity, "start": start, "end": end}) + "\n")
            trace.flush()
            clear_wait = traced_wait(clear, 'clear', identity)
            cs, ce = x.paint(w, gc, 0, 0)
            record_wait(clear_wait, cs, ce)
            trace.write(json.dumps({"event": "clear", "id": identity, "start": cs, "end": ce}) + "\n")
            trace.flush()
            events.append({"id": identity, "color": color, "onset_ns": onset,
                           "due_clear_ns": clear, "draw_start_ns": start,
                           "draw_end_ns": end, "clear_start_ns": cs, "clear_end_ns": ce})
        until(epoch + 1_050_000_000)
        final = x.capture(w)[3]
        write(root / "source.json", {"pid": os.getpid(), "window": w, "epoch_ns": epoch,
                                     "events": events, "wait_traces": source_waits, "final_pixels": final,
                                     "final_keymap": x.keymap()})
    finally:
        trace.close()
        wait_log.close()
        x.close()


if __name__ == "__main__":
    main()
