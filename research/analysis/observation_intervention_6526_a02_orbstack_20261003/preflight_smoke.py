from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tkinter as tk
from pathlib import Path

out = Path(os.environ.get("OUT_DIR", "/out"))
out.mkdir(parents=True, exist_ok=True)
root = tk.Tk()
root.title("6526 construction smoke")
tk.Label(root, text="private Xvfb construction only").pack()
root.update()
capture = subprocess.run(["xwd", "-root", "-silent"], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, timeout=10, check=False)
payload = capture.stdout
receipt = {"scope":"construction-only", "python":__import__("sys").version,
           "tk":root.tk.call("package", "provide", "Tk"),
           "display":os.environ.get("DISPLAY"), "xwd_exit":capture.returncode,
           "screenshot_bytes":len(payload), "screenshot_sha256":hashlib.sha256(payload).hexdigest()}
if capture.returncode != 0 or len(payload) < 1000:
    raise SystemExit(f"Xvfb screenshot smoke failed: {receipt}; {capture.stderr.decode(errors='replace')}")
(out/"xvfb-tk-smoke.json").write_text(json.dumps(receipt, sort_keys=True, indent=2)+"\n")
root.destroy()
print(json.dumps(receipt, sort_keys=True))
