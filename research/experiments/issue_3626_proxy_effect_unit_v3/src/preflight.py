"""Excluded GTK/Xvfb setup smoke; never runs or writes the 28-row formal allocation."""
import json, os, subprocess, tempfile, time
from pathlib import Path
from Xlib import X, display
from Xlib.ext import xtest

with tempfile.TemporaryDirectory(prefix="issue3610-preflight-") as td:
    rowdir=Path(td); disp=":302"; sock=Path("/tmp/.X11-unix/X302")
    xvfb=subprocess.Popen(["/usr/bin/Xvfb",disp,"-screen","0","640x480x24","-nolisten","tcp"],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    app=None; conn=None
    try:
        deadline=time.monotonic()+4
        while not sock.exists() and time.monotonic()<deadline: time.sleep(.02)
        if not sock.exists(): raise RuntimeError("Xvfb smoke socket missing")
        conn=display.Display(disp)
        env={**os.environ,"DISPLAY":disp,"ROW_DIR":td,"EFFECT_MODE":"on"}
        app=subprocess.Popen(["/usr/bin/python3","-B","/src/fixture.py"],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        win=None; deadline=time.monotonic()+4
        while time.monotonic()<deadline:
            for w in conn.screen().root.query_tree().children:
                try:
                    if (w.get_wm_name() or "").startswith("proxy-fixture:"): win=w; break
                except Exception: pass
            if win is not None: break
            time.sleep(.02)
        if win is None: raise RuntimeError("GTK smoke window missing")
        win.set_input_focus(X.RevertToParent,X.CurrentTime); conn.sync()
        xtest.fake_input(conn,X.MotionNotify,x=160,y=88); xtest.fake_input(conn,X.ButtonPress,1); xtest.fake_input(conn,X.ButtonRelease,1); conn.sync()
        deadline=time.monotonic()+2
        while time.monotonic()<deadline and (win.get_wm_name() or "").endswith(":0:1"): time.sleep(.02)
        title=win.get_wm_name()
        events=[json.loads(s) for s in (rowdir/"fixture-events.jsonl").read_text().splitlines()]
        result={"preflight":"PASS" if title=="proxy-fixture:1:2" and any(e.get("kind")=="effect" for e in events) else "STOP",
                "title":title,"events":events,"excluded_from_formal_matrix":True}
        print(json.dumps(result,sort_keys=True))
        if result["preflight"]!="PASS": raise SystemExit(1)
    finally:
        if app is not None:
            if app.poll() is None: app.terminate()
            app.wait(timeout=3)
        if conn is not None: conn.close()
        if xvfb.poll() is None: xvfb.terminate()
        xvfb.wait(timeout=3)
