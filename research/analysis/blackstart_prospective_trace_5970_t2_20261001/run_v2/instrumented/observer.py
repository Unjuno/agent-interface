#!/usr/bin/env python3
"""Additive test copy of archived X11 observer with explicit actuation IDs."""
import json
import os
import select
import sys
import time

from Xlib import X, display

xid = int(sys.argv[1], 0)
epoch = sys.argv[2]
out = sys.argv[3]
d = display.Display()
w = d.create_resource_object("window", xid)
w.change_attributes(event_mask=X.KeyPressMask | X.KeyReleaseMask)
d.sync()
km = d.query_keymap()
bootstrap = {
    "epoch": epoch,
    "mono_ns": time.monotonic_ns(),
    "keymap_hex": bytes(km).hex(),
}
print(
    json.dumps({"ready": True, "pid": os.getpid(), "epoch": epoch, "bootstrap": bootstrap}, sort_keys=True),
    flush=True,
)
fdx = d.fileno()
fdi = sys.stdin.fileno()
seq = 0
control_seq = 0
pending_id = None


def append(record):
    with open(out, "a", encoding="utf-8", buffering=1) as f:
        f.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")


running = True
while running:
    ready, _, _ = select.select([fdx, fdi], [], [], 0.1)
    if fdi in ready:
        line = sys.stdin.readline()
        if not line:
            break
        command = line.strip()
        if command == "stop":
            running = False
        elif command.startswith("arm:") and pending_id is None:
            control_seq += 1
            pending_id = command[4:]
            append(
                {
                    "kind": "arm_ack",
                    "consumer": "observer",
                    "control_seq": control_seq,
                    "actuation_id": pending_id,
                    "epoch": epoch,
                    "mono_ns": time.monotonic_ns(),
                }
            )
        else:
            control_seq += 1
            append(
                {
                    "kind": "arm_reject",
                    "consumer": "observer",
                    "control_seq": control_seq,
                    "command": command,
                    "pending_id": pending_id,
                    "epoch": epoch,
                    "mono_ns": time.monotonic_ns(),
                }
            )
    if fdx in ready:
        while d.pending_events():
            event = d.next_event()
            seq += 1
            if event.type in (X.KeyPress, X.KeyRelease):
                action_id = pending_id
                pending_id = None
                append(
                    {
                        "kind": "KeyPress" if event.type == X.KeyPress else "KeyRelease",
                        "source": "observer",
                        "source_seq": seq,
                        "event_id": f"observer:{epoch}:{seq}",
                        "actuation_id": action_id,
                        "causal_parent_ids": [f"act:{action_id}"] if action_id else [],
                        "epoch": epoch,
                        "keycode": int(event.detail),
                        "x_state": int(event.state),
                        "x_time": int(event.time),
                        "mono_ns": time.monotonic_ns(),
                    }
                )
if pending_id is not None:
    append(
        {
            "kind": "unconsumed_arm",
            "consumer": "observer",
            "actuation_id": pending_id,
            "epoch": epoch,
            "mono_ns": time.monotonic_ns(),
        }
    )
d.close()
