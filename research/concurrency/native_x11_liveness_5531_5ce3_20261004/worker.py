"""One preconnected native read, no restart, key or pointer operations."""
import json, os, sys, time
from pathlib import Path
from Xlib import display

def identity():
    return {'pid': os.getpid(), 'start_ticks': int(Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19]), 'nonce': sys.argv[2]}

def emit(kind, **fields):
    print(json.dumps({'kind': kind, **identity(), **fields}), flush=True)

d = display.Display(sys.argv[1])
emit('READY')
assert sys.stdin.readline().strip() == 'GO'
emit('QUERY_STARTED', query_started_ns=time.monotonic_ns())
reply = d.get_input_focus()
focus = reply.focus.id if hasattr(reply.focus, 'id') else int(reply.focus)
emit('RESULT', native_focus=focus, focus=focus + (1 if sys.argv[3] == 'invalid_response' else 0), query_finished_ns=time.monotonic_ns())
d.close()
