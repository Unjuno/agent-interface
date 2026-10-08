"""Confirmation fixture with attempt archive outside the temporary application dir."""
from pathlib import Path
import event_socket_v14 as bridge
original = bridge.subprocess.Popen
def spawn(args, **kwargs):
    args = list(args)
    index = next(i for i, a in enumerate(args) if str(a).endswith('interactive_v29.py'))
    args[index] = str(Path(__file__).with_name('confirmation_browser_entry_v3.py'))
    return original(args, **kwargs)
bridge.subprocess.Popen = spawn
bridge.main()
