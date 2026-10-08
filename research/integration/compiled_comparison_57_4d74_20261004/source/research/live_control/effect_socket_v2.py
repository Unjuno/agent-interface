"""Explicit cause candidate Inkscape entry behind private socket11 transport."""
from pathlib import Path
import sys
import event_socket_v11 as bridge
from effect_command_once_v1 import CommandOnce
bridge.CommandOnce=CommandOnce

HERE=Path(__file__).resolve().parent
ENTRIES={
    'inkscape':HERE/'effect_interactive_v1.py',
}
domain=sys.argv.pop(1)
if domain not in ENTRIES:raise SystemExit('domain must be inkscape')
original=bridge.subprocess.Popen
def spawn(args,**kwargs):
    args=list(args)
    index=next(i for i,a in enumerate(args) if str(a).endswith('interactive_v27.py'))
    args[index]=str(ENTRIES[domain])
    return original(args,**kwargs)
bridge.subprocess.Popen=spawn
bridge.main()
