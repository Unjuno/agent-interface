"""Changed-geometry OpenTTD L entrypoint behind private socket11 transport."""
from pathlib import Path
import sys

import event_socket_v11 as bridge


HERE = Path(__file__).resolve().parent
ENTRIES = {
    "openttd": HERE.parent / "openttd_task/interactive_l_v2.py",
}
domain = sys.argv.pop(1)
if domain not in ENTRIES:
    raise SystemExit("domain must be openttd")
original = bridge.subprocess.Popen


def spawn(args, **kwargs):
    args = list(args)
    index = next(i for i, value in enumerate(args) if str(value).endswith("interactive_v27.py"))
    args[index] = str(ENTRIES[domain])
    return original(args, **kwargs)


bridge.subprocess.Popen = spawn
bridge.main()
