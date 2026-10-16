"""Expose point-derived target handles behind socket11."""
from pathlib import Path
import sys

import event_socket_v11 as bridge


HERE = Path(__file__).resolve().parent
ENTRY = HERE / "interactive_target_handle_chromium_v5.py"
domain = sys.argv.pop(1)
if domain != "chromium-point-target-v1":
    raise SystemExit("domain must be chromium-point-target-v1")
original = bridge.subprocess.Popen


def spawn(args, **kwargs):
    args = list(args)
    index = next(index for index, value in enumerate(args)
                 if str(value).endswith("interactive_v27.py"))
    args[index] = str(ENTRY)
    return original(args, **kwargs)


bridge.subprocess.Popen = spawn
bridge.main()
