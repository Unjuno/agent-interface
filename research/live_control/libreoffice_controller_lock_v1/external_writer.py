#!/usr/bin/env /usr/bin/python3
import json, sys, time
import uno


def fail(msg):
    print(json.dumps({'ok': False, 'error': msg}, sort_keys=True))
    raise SystemExit(2)

if len(sys.argv) != 3:
    fail('usage: external_writer.py PORT TARGET_X')
port = int(sys.argv[1]); target_x = int(sys.argv[2])
ctx = uno.getComponentContext()
resolver = ctx.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver', ctx)
try:
    remote = resolver.resolve(f'uno:socket,host=127.0.0.1,port={port};urp;StarOffice.ComponentContext')
except Exception as e:
    fail(f'resolve:{type(e).__name__}:{e}')
smgr = remote.ServiceManager
desktop = smgr.createInstanceWithContext('com.sun.star.frame.Desktop', remote)
enum = desktop.getComponents().createEnumeration()
docs = []
while enum.hasMoreElements():
    c = enum.nextElement()
    if hasattr(c, 'getDrawPages'):
        docs.append(c)
if len(docs) != 1:
    fail(f'draw_doc_count={len(docs)}')
doc = docs[0]
page = doc.getDrawPages().getByIndex(0)
shape = None
for i in range(page.getCount()):
    s = page.getByIndex(i)
    if getattr(s, 'Name', '') == 'A':
        shape = s; break
if shape is None:
    fail('shape_A_missing')
lock_before = bool(doc.hasControllersLocked())
before = int(shape.getPosition().X)
p = shape.getPosition(); p.X = target_x
t0 = time.monotonic_ns()
shape.setPosition(p)
t1 = time.monotonic_ns()
after = int(shape.getPosition().X)
lock_after = bool(doc.hasControllersLocked())
print(json.dumps({
    'ok': True,
    'lock_seen_before': lock_before,
    'lock_seen_after': lock_after,
    'before_x': before,
    'requested_x': target_x,
    'after_x': after,
    'set_start_ns': t0,
    'set_end_ns': t1,
}, sort_keys=True))
