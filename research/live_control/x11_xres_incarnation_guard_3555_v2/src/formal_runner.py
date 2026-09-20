#!/usr/bin/env python3
"""Single formal XRes stale-alias allocation. All UI input is gated here."""
import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path

from Xlib import X, display

from incarnation_guard import admit


SRC = Path(__file__).resolve().parent
OUT = Path(os.environ["OUT_DIR"])
EFFECT = OUT / "effect.json"
FIXTURE = SRC / "fixture_window.py"
events = []
emissions = 0


def ticks_for(pid):
    stat = Path(f"/proc/{pid}/stat").read_text()
    return int(stat[stat.rfind(")") + 2 :].split()[19])


def start_fixture():
    env = dict(os.environ, EFFECT_PATH=str(EFFECT))
    process = subprocess.Popen(["python3", str(FIXTURE)], stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, env=env)
    line = process.stdout.readline().strip()
    match = re.fullmatch(r"READY pid=(\d+) xid=(\d+)", line)
    if not match:
        raise RuntimeError(f"fixture did not become ready: {line!r}")
    pid, xid = map(int, match.groups())
    dpy = display.Display()
    window = dpy.create_resource_object("window", xid)
    for _ in range(100):
        try:
            geom = window.get_geometry()
            image = window.get_image(0, 0, geom.width, geom.height, X.ZPixmap, 0xFFFFFFFF)
            if image is not None:
                break
        except Exception:
            pass
        time.sleep(0.02)
    else:
        raise RuntimeError("fixture window image unavailable")
    translated = dpy.screen().root.translate_coords(window, 0, 0)
    identity = {
        "xid": xid,
        "pid": pid,
        "start_ticks": ticks_for(pid),
        "geometry": [translated.x, translated.y, geom.width, geom.height, geom.depth],
        "pixel_sha256": hashlib.sha256(image.data).hexdigest(),
        "xres": json.loads(subprocess.check_output(["xres_owner", str(xid)], text=True)),
    }
    if identity["xres"]["pid"] != pid:
        raise RuntimeError("XRes PID does not match fixture PID")
    events.append({"event": "fixture_ready", "identity": identity})
    return process, dpy, window, identity


def bridge_click(dpy, identity):
    global emissions
    emissions += 1
    x, y, _, _, _ = identity["geometry"]
    subprocess.run(["xdotool", "mousemove", "--sync", str(x + 120), str(y + 76),
                    "click", "1"], check=True)
    dpy.sync()
    pointer = dpy.screen().root.query_pointer()
    return {"emissions": emissions, "button1_down_after": bool(pointer.mask & X.Button1Mask)}


def cleanup(*processes):
    for process in processes:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    first = second = None
    try:
        first, dpy1, win1, alias = start_fixture()
        first.terminate()
        first.wait(timeout=3)
        time.sleep(0.1)
        second, dpy2, win2, current = start_fixture()
        required_equal = ("xid", "geometry", "pixel_sha256")
        required_different = ("pid", "start_ticks")
        if (any(alias[key] != current[key] for key in required_equal)
                or any(alias[key] == current[key] for key in required_different)):
            events.append({"event": "preinput_precondition", "passed": False,
                           "p1": alias, "p2": current})
            raise RuntimeError("STOP_BEFORE_INPUT: identity reuse precondition failed")
        events.append({"event": "preinput_precondition", "passed": True})
        stale_admitted = admit(alias, current)
        events.append({"event": "stale_admission", "admitted": stale_admitted,
                       "bridge_called": False, "would_call_bridge": stale_admitted,
                       "emissions": emissions,
                       "effect_exists": EFFECT.exists()})
        if stale_admitted:
            raise RuntimeError("stale alias admitted; positive control suppressed")
        fresh_admitted = admit(current, current)
        if not fresh_admitted:
            raise RuntimeError("fresh identity refused")
        click_result = bridge_click(dpy2, current)
        for _ in range(100):
            if EFFECT.exists():
                break
            time.sleep(0.02)
        effect = json.loads(EFFECT.read_text()) if EFFECT.exists() else None
        events.append({"event": "fresh_positive_control", "admitted": fresh_admitted,
                       "bridge_called": True, "click": click_result, "effect": effect})
        if not effect or effect.get("count") != 1 or effect.get("pid") != current["pid"]:
            raise RuntimeError("fresh-control task effect missing")
        result = {"allocation": "issue3555-xres-guard-orbstack-v2-formal-01",
                  "status": "PASS_SCOPED_STALE_REFUSAL_AND_FRESH_CONTROL",
                  "events": events, "final_emissions": emissions}
    except Exception as exc:
        status = "STOP_BEFORE_INPUT" if str(exc).startswith("STOP_BEFORE_INPUT:") else "FAIL_OR_STOP"
        result = {"allocation": "issue3555-xres-guard-orbstack-v2-formal-01",
                  "status": status, "error": repr(exc), "events": events,
                  "final_emissions": emissions}
    finally:
        cleanup(first, second)
    (OUT / "raw.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    if result["status"] != "PASS_SCOPED_STALE_REFUSAL_AND_FRESH_CONTROL":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
