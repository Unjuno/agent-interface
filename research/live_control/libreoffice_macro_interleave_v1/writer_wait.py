#!/usr/bin/env /usr/bin/python3
import json
import sys
import time
from pathlib import Path
import uno


def fail(message):
    print(json.dumps({"ok": False, "error": message}, sort_keys=True))
    raise SystemExit(2)

if len(sys.argv) != 5:
    fail("usage: writer_wait.py PORT READY GO TARGET_X")
port = int(sys.argv[1])
ready = Path(sys.argv[2])
go = Path(sys.argv[3])
target_x = int(sys.argv[4])

ctx = uno.getComponentContext()
resolver = ctx.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", ctx)
try:
    remote = resolver.resolve(f"uno:socket,host=127.0.0.1,port={port};urp;StarOffice.ComponentContext")
except Exception as exc:
    fail(f"resolve:{type(exc).__name__}:{exc}")

desktop = remote.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", remote)
enum = desktop.getComponents().createEnumeration()
docs = []
while enum.hasMoreElements():
    component = enum.nextElement()
    if hasattr(component, "getDrawPages"):
        docs.append(component)
if len(docs) != 1:
    fail(f"draw_doc_count={len(docs)}")

page = docs[0].getDrawPages().getByIndex(0)
shape = None
for i in range(page.getCount()):
    candidate = page.getByIndex(i)
    if getattr(candidate, "Name", "") == "A":
        shape = candidate
        break
if shape is None:
    fail("shape_A_missing")

ready_ns = time.monotonic_ns()
ready.write_text(json.dumps({"ready_ns": ready_ns}) + "\n", encoding="utf-8")
while not go.exists():
    time.sleep(0.001)

go_seen_ns = time.monotonic_ns()
before_x = int(shape.getPosition().X)
pos = shape.getPosition()
pos.X = target_x
set_start_ns = time.monotonic_ns()
shape.setPosition(pos)
set_end_ns = time.monotonic_ns()
after_x = int(shape.getPosition().X)
print(json.dumps({
    "ok": True,
    "ready_ns": ready_ns,
    "go_seen_ns": go_seen_ns,
    "before_x": before_x,
    "requested_x": target_x,
    "set_call_start_ns": set_start_ns,
    "set_call_end_ns": set_end_ns,
    "after_x": after_x,
}, sort_keys=True))
