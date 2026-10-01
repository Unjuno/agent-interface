from __future__ import annotations
import argparse, json, os, sys, time, traceback
from pathlib import Path
import receiver

def enc(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), allow_nan=False)

def write_json(path: Path, obj):
    path.write_text(enc(obj)+"\n", encoding="utf-8")

ap = argparse.ArgumentParser()
ap.add_argument('--db', required=True)
ap.add_argument('--request', required=True)
ap.add_argument('--gate', required=True)
ap.add_argument('--ready', required=True)
ap.add_argument('--events', required=True)
ap.add_argument('--output', required=True)
ap.add_argument('--label', required=True)
a = ap.parse_args()
req = json.loads(Path(a.request).read_text(encoding='utf-8'))
ready_ns = time.monotonic_ns()
write_json(Path(a.ready), {'label':a.label,'pid':os.getpid(),'ready_ns':ready_ns})
try:
    while not Path(a.gate).exists():
        time.sleep(0.0001)
    gate_seen_ns = time.monotonic_ns()
    call_enter_ns = time.monotonic_ns()
    result = receiver.receive(a.db, req, 'outcome_first', 'none', a.events)
    call_exit_ns = time.monotonic_ns()
    out = {'ok':True,'label':a.label,'pid':os.getpid(),'ready_ns':ready_ns,
           'gate_seen_ns':gate_seen_ns,'call_enter_ns':call_enter_ns,'call_exit_ns':call_exit_ns,
           'result':result}
    write_json(Path(a.output), out)
except BaseException as exc:
    call_exit_ns = time.monotonic_ns()
    out = {'ok':False,'label':a.label,'pid':os.getpid(),'ready_ns':ready_ns,
           'call_exit_ns':call_exit_ns,'error_type':type(exc).__name__,'error':str(exc),
           'traceback':traceback.format_exc()}
    write_json(Path(a.output), out)
    raise
