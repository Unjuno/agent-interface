from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import Xlib
from Xlib import XK, display

OUT = Path(sys.argv[1])
ALLOCATION = "issue3733-german-xkb-map-diagnostic-formal-01"
IMAGE = "agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27"
BASE = "e9198a1c74ef4ca2759e92c4539b10dbe3a20ba8"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def command(args: list[str], env: dict[str, str]) -> dict:
    p = subprocess.run(args, env=env, capture_output=True, text=True, timeout=12)
    return {"argv": args, "returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr}


def xlib_map(name: str) -> dict:
    d = display.Display(name)
    i = d.display.info
    rows = [list(x) for x in d.get_keyboard_mapping(i.min_keycode, i.max_keycode-i.min_keycode+1)]
    keysyms = {}
    for label, symbol in (("y", "y"), ("z", "z"), ("equal", "equal"), ("asterisk", "asterisk")):
        code = d.keysym_to_keycode(XK.string_to_keysym(symbol))
        keysyms[label] = {"keycode": int(code), "level0": int(d.keycode_to_keysym(code, 0)), "level1": int(d.keycode_to_keysym(code, 1))}
    d.close()
    return {"min_keycode": i.min_keycode, "max_keycode": i.max_keycode, "mapping": rows, "keysyms": keysyms, "mapping_sha256": sha(json.dumps(rows, separators=(",", ":")).encode())}


def capture(case: str, layout: str, number: int) -> dict:
    root = OUT / case
    root.mkdir(parents=True, exist_ok=False)
    name = f":{number}"
    env = os.environ.copy(); env["DISPLAY"] = name
    log = (root / "xvfb.log").open("wb")
    xv = subprocess.Popen(["/usr/bin/Xvfb", name, "-screen", "0", "800x600x24", "-nolisten", "tcp", "+extension", "XKEYBOARD", "+extension", "XTEST"], env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
    row = {"case": case, "requested_layout": layout, "display": name, "xvfb_pid": xv.pid, "status": "STOP_SETUP"}
    try:
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            if xv.poll() is not None: raise RuntimeError(f"XVFB_EXIT:{xv.returncode}")
            try: d = display.Display(name); break
            except Exception: time.sleep(.05)
        else: raise RuntimeError("XVFB_CONNECT_TIMEOUT")
        row["extensions"] = {"XKEYBOARD": bool(d.query_extension("XKEYBOARD").present), "XTEST": bool(d.has_extension("XTEST"))}
        d.close()
        if not all(row["extensions"].values()): raise RuntimeError("X11_EXTENSION_MISSING")
        before = {}
        for label, argv in (("query", ["setxkbmap", "-query"]), ("xkbcomp", ["xkbcomp", "-xkb", name, "-"]), ("xmodmap", ["xmodmap", "-pke"])):
            before[label] = command(argv, env)
            (root / f"before.{label}.txt").write_text(before[label]["stdout"])
        before["xlib"] = xlib_map(name)
        (root / "before.xlib.json").write_text(json.dumps(before["xlib"], indent=2, sort_keys=True)+"\n")
        row["before"] = before
        if layout == "de":
            row["apply"] = command(["setxkbmap", "-layout", "de"], env)
            after = {}
            for label, argv in (("query", ["setxkbmap", "-query"]), ("xkbcomp", ["xkbcomp", "-xkb", name, "-"]), ("xmodmap", ["xmodmap", "-pke"])):
                after[label] = command(argv, env)
                (root / f"after.{label}.txt").write_text(after[label]["stdout"])
            after["xlib"] = xlib_map(name)
            (root / "after.xlib.json").write_text(json.dumps(after["xlib"], indent=2, sort_keys=True)+"\n")
            row["after"] = after
            q = re.search(r"(?m)^layout:\s*(\S+)", after["query"]["stdout"])
            row["query_layout"] = q.group(1) if q else None
            row["methods_changed"] = {
                "xkbcomp": before["xkbcomp"]["stdout"] != after["xkbcomp"]["stdout"],
                "xmodmap": before["xmodmap"]["stdout"] != after["xmodmap"]["stdout"],
                "xlib_full_map": before["xlib"]["mapping"] != after["xlib"]["mapping"],
                "xlib_selected_symbols": before["xlib"]["keysyms"] != after["xlib"]["keysyms"],
            }
            row["status"] = "OBSERVED"
        else:
            row["after"] = before
            row["query_layout"] = "us"
            row["methods_changed"] = {"xkbcomp": False, "xmodmap": False, "xlib_full_map": False, "xlib_selected_symbols": False}
            row["status"] = "CONTROL"
    except Exception as exc:
        row["error"] = f"{type(exc).__name__}:{exc}"
    finally:
        if xv.poll() is None: xv.terminate()
        try: rc = xv.wait(timeout=4)
        except subprocess.TimeoutExpired: xv.kill(); rc = xv.wait(timeout=4)
        log.flush(); log.close()
        row["xvfb_process"] = {"pid": xv.pid, "returncode": rc, "reaped": xv.poll() is not None}
        row["xvfb_log_sha256"] = sha((root/"xvfb.log").read_bytes())
    return row


def main() -> int:
    if any(OUT.iterdir()): raise SystemExit("STOP_OUTPUT_NOT_EMPTY")
    OUT.mkdir(parents=True, exist_ok=True)
    rows = [capture("german", "de", 161), capture("us-control", "us", 162)]
    artifacts = {p.relative_to(OUT).as_posix(): sha(p.read_bytes()) for p in sorted(OUT.rglob("*")) if p.is_file() and p.name != "raw.json"}
    raw = {"allocation": ALLOCATION, "base_commit": BASE, "image": IMAGE, "platform": "linux/arm64", "network": "none", "xlib_version": str(getattr(Xlib,"__version__","unknown")), "rows": rows, "artifact_sha256": artifacts, "disposition": "OBSERVED_PENDING_AUDIT" if all(r["status"] in {"OBSERVED","CONTROL"} for r in rows) else "STOP"}
    (OUT/"raw.json").write_text(json.dumps(raw, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"allocation": ALLOCATION, "disposition": raw["disposition"], "rows": [{"case":r["case"],"status":r["status"]} for r in rows]}, sort_keys=True))
    return 0


if __name__ == "__main__": raise SystemExit(main())
