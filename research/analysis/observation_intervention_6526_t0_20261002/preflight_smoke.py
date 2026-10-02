"""Construction-only smoke for Tk/Xvfb and private-display screenshot capture."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tkinter as tk
from pathlib import Path


OUT = Path(os.environ.get("OUT_DIR", "/out"))
OUT.mkdir(parents=True, exist_ok=True)

root = tk.Tk()
root.title("6526 private Xvfb smoke")
tk.Label(root, text="private-display construction smoke", padx=12, pady=8).pack()
root.update_idletasks()
root.update()

image = OUT / "tk-root.xwd"
subprocess.run(["xwd", "-root", "-silent", "-out", str(image)], check=True, timeout=10)
payload = image.read_bytes()
if len(payload) < 100:
    raise SystemExit(f"screenshot payload too small: {len(payload)} bytes")

receipt = {
    "schema": "issue6526-wslc-gui-preflight-v1",
    "claim": "construction capability only; not an observation-intervention experiment",
    "python": __import__("sys").version,
    "tcl": root.tk.call("info", "patchlevel"),
    "tk": root.tk.call("package", "provide", "Tk"),
    "display": os.environ.get("DISPLAY"),
    "window_geometry": root.geometry(),
    "screenshot_bytes": len(payload),
    "screenshot_sha256": hashlib.sha256(payload).hexdigest(),
}
(OUT / "preflight.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps(receipt, sort_keys=True))
root.destroy()
