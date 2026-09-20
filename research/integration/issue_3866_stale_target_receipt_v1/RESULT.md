#!/usr/bin/python3
"""Independent XRecord observer for core keyboard/button events."""
import argparse
import json
from pathlib import Path
import threading
import time

from Xlib import X
from Xlib.display import Display
from Xlib.ext import record
from Xlib.protocol import rq


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--display", required=True)
    ap.add_argument("--events", required=True, type=Path)
    ap.add_argument("--ready", required=True, type=Path)
    ap.add_argument("--stop", required=True, type=Path)
    args = ap.parse_args()
    d = Display(args.display)
    ended = False
    count = 0
    start_event = threading.Event()
    errors = []

    def on_reply(reply):
        nonlocal ended, count
        if reply.category == record.StartOfData:
            start_event.set()
            args.ready.write_text(json.dumps({"ready": True,
                                              "category": "StartOfData"})+"\n")
        elif reply.category == record.FromServer:
            data = reply.data
            while len(data):
                event, data = rq.EventField(None).parse_binary_value(
                    data, d.display, None, None)
                etype = event.type & 0x7f
                if etype in (X.KeyPress, X.KeyRelease,
                             X.ButtonPress, X.ButtonRelease):
                    row = {"type": etype, "detail": event.detail,
                           "sequence": getattr(event, "sequence_number", None),
                           "record_category": "FromServer"}
                    with args.events.open("a", encoding="utf-8") as f:
                        f.write(json.dumps(row, sort_keys=True)+"\n")
                    count += 1
        elif reply.category == record.EndOfData:
            ended = True

    context = d.record_create_context(0, [record.AllClients], [{
        "core_requests": (0, 0), "core_replies": (0, 0),
        "ext_requests": (0, 0, 0, 0), "ext_replies": (0, 0, 0, 0),
        "delivered_events": (0, 0),
        "device_events": (X.KeyPress, X.ButtonRelease),
        "errors": (0, 0), "client_started": False, "client_died": False,
    }])
    def enable():
        try:
            # This python-xlib request blocks until EndOfData; keep the
            # recording connection devoted to its response stream.
            d.record_enable_context(context, on_reply)
        except Exception as exc:  # retained by the parent process as STOP
            errors.append(repr(exc))

    thread = threading.Thread(target=enable, name="xrecord-enable", daemon=True)
    thread.start()
    deadline = time.monotonic()+10
    if not start_event.wait(max(0, deadline-time.monotonic())):
        raise TimeoutError("XRecord StartOfData not received")
    while not args.stop.exists():
        time.sleep(0.02)
    # Disable through a second client so the RECORD reply reader can finish
    # its blocking multi-reply request and deliver EndOfData.
    control = Display(args.display)
    control.record_disable_context(context)
    control.sync()
    control.close()
    thread.join(5)
    if thread.is_alive():
        d.close()
        thread.join(2)
        raise TimeoutError("XRecord enable request did not terminate")
    d.record_free_context(context)
    args.ready.write_text(json.dumps({"ready": True, "ended": ended,
                                      "event_count": count,
                                      "errors": errors})+"\n")
    d.close()
    if not ended or errors:
        raise TimeoutError("XRecord EndOfData not received")


if __name__ == "__main__":
    main()

