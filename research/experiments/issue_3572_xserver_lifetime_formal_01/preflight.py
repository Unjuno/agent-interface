from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from Xlib import X, display


SOCKET = Path("/tmp/.X11-unix/X149")


def launch():
    proc = subprocess.Popen(["Xvfb", ":149", "-screen", "0", "640x480x24", "-nolisten", "tcp", "-ac"],
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline and not SOCKET.exists():
        if proc.poll() is not None:
            raise RuntimeError(proc.stderr.read().decode("utf-8", "replace"))
        time.sleep(0.02)
    if not SOCKET.exists():
        proc.terminate()
        proc.wait(timeout=3)
        raise RuntimeError("socket did not appear")
    d = display.Display(":149")
    root = d.screen().root
    w = root.create_window(20, 20, 100, 60, 1, d.screen().root_depth, X.InputOutput, X.CopyFromParent)
    w.set_wm_name("typed-recovery-lifetime")
    w.set_wm_class("typed-recovery-lifetime", "TypedRecoveryFixture")
    w.map()
    d.sync()
    out = {"pid": proc.pid, "root_xid": int(root.id), "window_xid": int(w.id),
           "title": w.get_wm_name(), "class": list(w.get_wm_class() or [])}
    w.destroy()
    d.sync()
    d.close()
    proc.terminate()
    proc.wait(timeout=5)
    deadline = time.monotonic() + 5
    while SOCKET.exists() and time.monotonic() < deadline:
        time.sleep(0.02)
    out.update({"exit_code": proc.returncode, "socket_disappeared": not SOCKET.exists()})
    return out


first = launch()
second = launch()
result = {"kind": "construction-only-xvfb-preflight", "formal_invocation": False,
          "generations": [first, second],
          "root_xid_reused": first["root_xid"] == second["root_xid"],
          "window_xid_reused": first["window_xid"] == second["window_xid"],
          "same_fixture_metadata": first["title"] == second["title"] and first["class"] == second["class"]}
print(json.dumps(result, sort_keys=True))
if not (result["root_xid_reused"] and result["window_xid_reused"] and result["same_fixture_metadata"]
        and all(g["exit_code"] == 0 and g["socket_disappeared"] for g in result["generations"])):
    raise SystemExit(2)
