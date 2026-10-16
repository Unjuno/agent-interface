"""Unchanged v9 domain entrypoints behind existing private socket11 transport."""
from pathlib import Path
import sys
import event_socket_v11 as bridge

HERE=Path(__file__).resolve().parent
ENTRIES={
    'inkscape':HERE/'interactive_v11.py',
    'openttd':HERE.parent/'openttd_task/interactive_v2.py',
    'mindustry':HERE.parent/'benchmark_discovery/mindustry_build_interactive_v1.py',
}
domain=sys.argv.pop(1)
if domain not in ENTRIES:raise SystemExit('domain must be inkscape/openttd/mindustry')
original=bridge.subprocess.Popen
def spawn(args,**kwargs):
    args=list(args)
    index=next(i for i,a in enumerate(args) if str(a).endswith('interactive_v27.py'))
    args[index]=str(ENTRIES[domain])
    return original(args,**kwargs)
bridge.subprocess.Popen=spawn
bridge.main()
