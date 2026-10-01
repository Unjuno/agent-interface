"""Record a single real module invocation; audit hooks are not a sandbox."""
import json
import os
from pathlib import Path
import runpy
import sys
import time

program_path, trace_path = sys.argv[1:]
events = []
watching = True


def hook(event, args):
    if watching and (event.startswith(("socket.", "subprocess.", "ctypes.dlopen"))
                     or event in {"os.system", "os.fork", "os.exec", "os.posix_spawn"}):
        events.append(event)


sys.addaudithook(hook)
started = time.monotonic_ns()
code = 0
sys.argv = ["runtime.cli_v1.validate_program", "--program", program_path]
try:
    runpy.run_module("runtime.cli_v1.validate_program", run_name="__main__")
except SystemExit as exit_result:
    code = exit_result.code
finally:
    watching = False
    trace = {
        "pid": os.getpid(), "ppid": os.getppid(),
        "started_ns": started, "ended_ns": time.monotonic_ns(),
        "exit_code": code, "events": events,
        "native_modules": sorted(n for n in sys.modules
                                 if n.startswith(("runtime.backends", "Xlib", "tkinter", "PIL"))),
        "runtime_modules": sorted(n for n in sys.modules if n.startswith("runtime.")),
        "no_site": sys.flags.no_site, "display": os.environ.get("DISPLAY"),
        "wayland_display": os.environ.get("WAYLAND_DISPLAY"),
    }
    Path(trace_path).write_text(json.dumps(trace, sort_keys=True, indent=2) + "\n", encoding="utf-8")
raise SystemExit(code)
