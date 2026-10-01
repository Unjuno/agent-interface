"""RuntimeClient socket entrypoint retaining main's integrated fixture adapter."""
from pathlib import Path
import os
import sys
LIVE=Path(os.environ["ISSUE3824_LIVE_SOURCE"]).resolve()
if not LIVE.is_dir() or not (LIVE/"event_socket_v11.py").is_file():
    raise SystemExit("STOP_LIVE_RUNTIME_SOURCE_MISSING:"+str(LIVE))
sys.path.insert(0,str(LIVE))
import event_socket_v11 as bridge
ENTRY=LIVE/"interactive_integrated_efficiency_v1.py"
if not ENTRY.is_file(): raise SystemExit("STOP_INTEGRATED_FIXTURE_ENTRY_MISSING:"+str(ENTRY))
domain=sys.argv.pop(1)
if domain!="integrated-efficiency-chromium-v1": raise SystemExit("unexpected fixture domain")
original=bridge.subprocess.Popen
def spawn(args, **kwargs):
    args=list(args)
    index=next(i for i,value in enumerate(args) if str(value).endswith("interactive_v27.py"))
    args[index]=str(ENTRY)
    return original(args, **kwargs)
bridge.subprocess.Popen=spawn
bridge.main()
