"""Expose the changed-save target/guard OpenTTD protocol behind socket11."""
from pathlib import Path
import sys

import event_socket_v11 as bridge


HERE = Path(__file__).resolve().parent
ENTRY = HERE.parent / "openttd_task/interactive_l_target_guard_v2.py"
domain = sys.argv.pop(1)
if domain != "openttd-target-guard-geometry-v2":
    raise SystemExit("domain must be openttd-target-guard-geometry-v2")
original = bridge.subprocess.Popen


def spawn(args, **kwargs):
    args = list(args)
    index = next(index for index, value in enumerate(args)
                 if str(value).endswith("interactive_v27.py"))
    args[index] = str(ENTRY)
    return original(args, **kwargs)


bridge.subprocess.Popen = spawn
bridge.main()
