#!/usr/bin/env python3
import argparse,json,sys,time
from pathlib import Path
from Xlib import display
import preflight_dependency as dep
ap=argparse.ArgumentParser();ap.add_argument('--rows',type=Path,required=True);ap.add_argument('--first',type=int,required=True);a=ap.parse_args()
d=display.Display(); rows=json.loads(a.rows.read_text())
print(json.dumps({'ready_ns':time.monotonic_ns()}),flush=True)
line=sys.stdin.readline()
if line.strip()!='go': raise SystemExit('expected go')
start=time.monotonic_ns(); print(json.dumps({'request_start_ns':start}),flush=True)
d.change_keyboard_mapping(a.first,[tuple(r) for r in rows]); d.sync()
applied=dep.fingerprint(dep.keyboard_mapping(d)); done=time.monotonic_ns(); print(json.dumps({'request_done_ns':done,'applied_hash':applied}),flush=True)
d.close()
