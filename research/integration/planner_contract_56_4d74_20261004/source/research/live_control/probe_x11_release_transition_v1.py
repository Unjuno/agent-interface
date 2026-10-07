"""Finite Xvfb probe for caller-bracketed queued X11 key-release semantics.

The worker thread exclusively owns the X display, mirroring the architectural
property of InputOwner v10. The caller brackets a queued release request without
performing any pre-release state query; physical state is checked only after the
worker has synchronized the release.
"""
import argparse
import json
import queue
import statistics
import threading
import time

from Xlib import X, XK, display
from Xlib.ext import xtest


def percentile(values, p):
    ordered = sorted(values)
    if not ordered:
        raise ValueError("empty sample")
    rank = (len(ordered) - 1) * p
    lo = int(rank)
    hi = min(lo + 1, len(ordered) - 1)
    fraction = rank - lo
    return int(round(ordered[lo] * (1 - fraction) + ordered[hi] * fraction))


class MiniOwner:
    def __init__(self, display_name):
        self.display_name = display_name
        self.requests = queue.Queue()
        self.ready = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=False)
        self.thread.start()
        if not self.ready.wait(2):
            raise RuntimeError("mini owner startup timeout")

    def call(self, operation):
        done = threading.Event()
        reply = []
        self.requests.put((operation, done, reply))
        if not done.wait(2):
            raise RuntimeError("mini owner reply timeout")
        ok, value = reply[0]
        if not ok:
            raise value
        return value

    def close(self):
        self.call("close")
        self.thread.join(2)
        if self.thread.is_alive():
            raise RuntimeError("mini owner failed to close")

    def _run(self):
        d = display.Display(self.display_name)
        root = d.screen().root
        window = root.create_window(20, 20, 120, 80, 0, d.screen().root_depth,
                                    X.InputOutput, X.CopyFromParent,
                                    background_pixel=d.screen().white_pixel,
                                    event_mask=X.FocusChangeMask)
        window.map(); d.sync(); window.set_input_focus(X.RevertToParent, X.CurrentTime); d.sync()
        code = d.keysym_to_keycode(XK.string_to_keysym("a"))
        self.ready.set()
        try:
            while True:
                operation, done, reply = self.requests.get()
                try:
                    if operation == "down":
                        admitted_ns = time.perf_counter_ns()
                        xtest.fake_input(d, X.KeyPress, code); d.sync()
                        value = {"admitted_ns": admitted_ns,
                                 "input_ack_ns": time.perf_counter_ns()}
                    elif operation == "up":
                        xtest.fake_input(d, X.KeyRelease, code); d.sync()
                        value = None
                    elif operation == "physical_down":
                        bitmap = d.query_keymap()
                        value = bool(bitmap[code // 8] & (1 << (code % 8)))
                    elif operation == "close":
                        value = None
                    else:
                        raise ValueError(operation)
                    reply.append((True, value))
                except BaseException as exc:
                    reply.append((False, exc))
                finally:
                    done.set()
                if operation == "close":
                    break
        finally:
            window.destroy(); d.sync(); d.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--display", required=True)
    parser.add_argument("--trials", type=int, default=100)
    args = parser.parse_args()
    if args.trials < 1:
        raise ValueError("trials must be positive")

    owner = MiniOwner(args.display)
    widths = []
    samples = []
    try:
        for index in range(args.trials):
            admission = owner.call("down")
            down_verified = owner.call("physical_down")
            # No physical-state query occurs between this timestamp and the up
            # request. The caller bracket includes queue scheduling + XTest + sync.
            release_call_started_ns = time.perf_counter_ns()
            owner.call("up")
            release_call_returned_ns = time.perf_counter_ns()
            up_verified = not owner.call("physical_down")
            width_ns = release_call_returned_ns - release_call_started_ns
            widths.append(width_ns)
            samples.append({"trial": index, **admission,
                            "release_call_started_ns": release_call_started_ns,
                            "release_call_returned_ns": release_call_returned_ns,
                            "release_window_ns": width_ns,
                            "down_verified": down_verified,
                            "up_verified": up_verified})
            if not down_verified or not up_verified:
                raise AssertionError("XQueryKeymap state verification failed")
    finally:
        owner.close()

    result = {"schema": "x11-release-transition-probe-v1",
              "architecture": "caller -> queue -> exclusive X11 owner thread -> d.sync",
              "pre_release_observation": False,
              "display": args.display,
              "trials": args.trials,
              "all_down_verified": all(sample["down_verified"] for sample in samples),
              "all_up_verified": all(sample["up_verified"] for sample in samples),
              "release_window_ns": {
                  "min": min(widths),
                  "median": int(statistics.median(widths)),
                  "p95": percentile(widths, .95),
                  "p99": percentile(widths, .99),
                  "max": max(widths),
              },
              "samples": samples}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
