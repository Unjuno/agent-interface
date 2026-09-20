"""Excluded GTK/Xvfb setup smoke; never runs or writes the 28-row formal allocation."""
import json, os, subprocess, tempfile, time
from pathlib import Path
from Xlib import X, display
from Xlib.ext import res, xtest
from proxy import blue_bbox, center
from runner import ximage_rgb

with tempfile.TemporaryDirectory(prefix="issue3631-preflight-") as td:
    rowdir=Path(td); disp=":302"; sock=Path("/tmp/.X11-unix/X302")
    xvfb=subprocess.Popen(["/usr/bin/Xvfb",disp,"-screen","0","640x480x24","-nolisten","tcp"],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    app=None; ambiguous_app=None; conn=None
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
        eventfile=rowdir/"fixture-events.jsonl"
        ready=next(json.loads(s) for s in eventfile.read_text().splitlines() if json.loads(s).get("kind")=="ready")
        owner, _=res.ClientIdSpec.parse_binary(res.ClientIdSpec.to_binary(client=int(win.id),mask=res.LocalClientPIDMask),conn)
        owner_reply=conn.res_query_client_ids([owner])
        pids=[item.value[0] for item in owner_reply.ids if item.spec.mask==res.LocalClientPIDMask]
        if pids != [ready["pid"]] or ready["pid"] != app.pid: raise RuntimeError("preflight XRes owner mismatch")
        initial_xres_pid=pids[0]
        rect=ready["button_rect"]; x=rect["x"]+rect["width"]//2; y=rect["y"]+rect["height"]//2
        geom=win.get_geometry(); image=win.get_image(0,0,geom.width,geom.height,X.ZPixmap,0xFFFFFFFF)
        rgb,pixel_meta=ximage_rgb(conn,image,geom.width,geom.height)
        screenshot_coordinate=center(blue_bbox(geom.width,geom.height,rgb))
        if screenshot_coordinate != [x,y]: raise RuntimeError(f"screenshot target mismatch {screenshot_coordinate} != {[x,y]} ({pixel_meta})")
        win.set_input_focus(X.RevertToParent,X.CurrentTime); conn.sync()
        xtest.fake_input(conn,X.MotionNotify,x=x,y=y); xtest.fake_input(conn,X.ButtonPress,1); xtest.fake_input(conn,X.ButtonRelease,1); conn.sync()
        deadline=time.monotonic()+2
        while time.monotonic()<deadline and (win.get_wm_name() or "").endswith(":0:1"): time.sleep(.02)
        title=win.get_wm_name()
        events=[json.loads(s) for s in (rowdir/"fixture-events.jsonl").read_text().splitlines()]
        acknowledged=sum(e.get("kind")=="click_ack" for e in events)
        effects=sum(e.get("kind")=="effect" for e in events)
        env2={**os.environ,"DISPLAY":disp,"ROW_DIR":td,"EFFECT_MODE":"on"}
        ambiguous_app=subprocess.Popen(["/usr/bin/python3","-B","/src/fixture.py"],env=env2,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        deadline=time.monotonic()+3; targets=[]; owner_pids=[]
        while time.monotonic()<deadline:
            targets=[]
            for candidate in conn.screen().root.query_tree().children:
                try:
                    if (candidate.get_wm_name() or "").startswith("proxy-fixture:") and candidate.get_attributes().map_state==X.IsViewable:
                        owner_spec,_=res.ClientIdSpec.parse_binary(res.ClientIdSpec.to_binary(client=int(candidate.id),mask=res.LocalClientPIDMask),conn)
                        owner_reply=conn.res_query_client_ids([owner_spec])
                        pids=[item.value[0] for item in owner_reply.ids if item.spec.mask==res.LocalClientPIDMask]
                        targets.append(candidate)
                        owner_pids.extend(pids)
                except Exception: pass
            ready_pids=sorted(json.loads(s).get("pid") for s in eventfile.read_text().splitlines() if json.loads(s).get("kind")=="ready")
            if len(targets)==2 and len(set(int(w.id) for w in targets))==2 and sorted(owner_pids)==ready_pids==sorted([app.pid,ambiguous_app.pid]): break
            owner_pids=[]; time.sleep(.02)
        ambiguous_ok=len(targets)==2 and len(set(int(w.id) for w in targets))==2 and sorted(owner_pids)==sorted([app.pid,ambiguous_app.pid])
        ambiguous_app.terminate(); ambiguous_app.wait(timeout=3); ambiguous_app=None
        events_after=[json.loads(s) for s in eventfile.read_text().splitlines()]
        ambiguity_no_action=(sum(e.get("kind")=="click_ack" for e in events_after)==acknowledged and sum(e.get("kind")=="effect" for e in events_after)==effects)
        release=conn.screen().root.query_pointer()
        result={"preflight":"PASS" if title=="proxy-fixture:1:2" and any(e.get("kind")=="effect" for e in events) and ambiguous_ok and ambiguity_no_action and not (release.mask & X.Button1Mask) else "STOP",
                "title":title,"events":events,"initial_xres_pid":initial_xres_pid,"derived_coordinate":[x,y],
                "screenshot_coordinate":screenshot_coordinate,"pixel_meta":pixel_meta,
                "ambiguity_gate":{"two_distinct_xids":len(targets)==2,"xres_pids":sorted(owner_pids),"ready_pids":sorted(ready_pids),"no_new_ack_or_effect":ambiguity_no_action},
                "release_verified":not bool(release.mask & X.Button1Mask),"excluded_from_formal_matrix":True}
        output=Path(os.environ["PREFLIGHT_OUTPUT"])
        output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
        print(json.dumps(result,sort_keys=True))
        if result["preflight"]!="PASS": raise SystemExit(1)
    finally:
        if ambiguous_app is not None:
            if ambiguous_app.poll() is None: ambiguous_app.terminate()
            ambiguous_app.wait(timeout=3)
        if app is not None:
            if app.poll() is None: app.terminate()
            app.wait(timeout=3)
        if conn is not None: conn.close()
        if xvfb.poll() is None: xvfb.terminate()
        xvfb.wait(timeout=3)
