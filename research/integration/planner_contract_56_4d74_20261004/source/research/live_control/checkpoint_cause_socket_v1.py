"""Explicit cause candidate Inkscape entry behind private socket11 transport."""
from pathlib import Path
import sys
import stopped_socket_v2 as bridge
from checkpoint_cause_cursor_v1 import EventCursor
from command_once_v3 import CommandOnce
bridge.EventCursor=EventCursor
bridge.CommandOnce=CommandOnce

HERE=Path(__file__).resolve().parent
ENTRIES={
    'chromium':HERE/'checkpoint_cause_interactive_v1.py',
    'calc':HERE/'checkpoint_cause_interactive_v1.py',
    'inkscape':HERE/'checkpoint_cause_interactive_v1.py',
}
domain=sys.argv.pop(1)
if domain not in ENTRIES:raise SystemExit('domain must be inkscape, calc or chromium')
original=bridge.subprocess.Popen
def spawn(args,**kwargs):
    args=list(args)
    index=next(i for i,a in enumerate(args) if str(a).endswith('interactive_v27.py'))
    args[index]=str(ENTRIES[domain])
    return original(args,**kwargs)
bridge.subprocess.Popen=spawn
bridge.main()
