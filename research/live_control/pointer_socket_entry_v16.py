"""Expose the scoped target-handle OpenTTD candidate behind socket11."""
from pathlib import Path
import sys

import event_socket_v11 as bridge


HERE = Path(__file__).resolve().parent
ENTRY = HERE.parent / "openttd_task/interactive_l_target_handle_v1.py"
domain = sys.argv.pop(1)
if domain != "openttd-target-handle-live-v1":
    raise SystemExit("domain must be openttd-target-handle-live-v1")
original = bridge.subprocess.Popen


def spawn(args, **kwargs):
    args = list(args)
    index = next(index for index, value in enumerate(args)
                 if str(value).endswith("interactive_v27.py"))
    args[index] = str(ENTRY)
    return original(args, **kwargs)


bridge.subprocess.Popen = spawn
bridge.main()
