"""Test-only prefilled form fixture inside frozen socket v11/runtime v27."""
from pathlib import Path
import event_socket_v11 as bridge
original=bridge.subprocess.Popen
def spawn(args,**kwargs):
    args=list(args);index=next(i for i,a in enumerate(args) if str(a).endswith('interactive_v27.py'))
    args[index]=str(Path(__file__).with_name('prefilled_browser_entry.py'))
    return original(args,**kwargs)
bridge.subprocess.Popen=spawn
bridge.main()
