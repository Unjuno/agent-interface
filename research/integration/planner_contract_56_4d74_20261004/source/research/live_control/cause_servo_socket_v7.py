"""Explicit cause candidate Inkscape entry behind private socket11 transport."""
from pathlib import Path
import sys
import stopped_socket_v2 as bridge

HERE=Path(__file__).resolve().parent
ENTRIES={
    'chromium':HERE/'cause_servo_interactive_v5.py',
    'calc':HERE/'cause_servo_interactive_v5.py',
    'inkscape':HERE/'cause_servo_interactive_v5.py',
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
