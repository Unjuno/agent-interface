#!/usr/bin/env python3
"""Single-allocation Xvfb/GTK event-prefix experiment; no network required."""
import hashlib, json, os, subprocess, time
from pathlib import Path
from Xlib import X, display
from Xlib.ext import xtest

CASES = {
 "valid": [{"kind":"obs","gen":1,"seq":1,"target":"A","value":True}],
 "true_then_revoke": [{"kind":"obs","gen":1,"seq":1,"target":"A","value":True},{"kind":"revoke","gen":1,"seq":2,"target":"A"}],
 "revoke_first": [{"kind":"revoke","gen":1,"seq":1,"target":"A"},{"kind":"obs","gen":1,"seq":2,"target":"A","value":True}],
 "replacement_delayed_old": [{"kind":"replace","gen":2,"seq":1,"target":"B"},{"kind":"obs","gen":1,"seq":2,"target":"A","value":True}],
 "out_of_order_false": [{"kind":"obs","gen":1,"seq":3,"target":"A","value":True},{"kind":"obs","gen":1,"seq":2,"target":"A","value":False}],
 "duplicate_true": [{"kind":"obs","gen":1,"seq":1,"target":"A","value":False},{"kind":"obs","gen":1,"seq":2,"target":"A","value":True},{"kind":"obs","gen":1,"seq":2,"target":"A","value":True}],
 "restart_replay": [{"kind":"obs","gen":1,"seq":1,"target":"A","value":True},{"kind":"restart","gen":2,"seq":0,"target":"A"},{"kind":"obs","gen":1,"seq":1,"target":"A","value":True}],
 "effect_off": [{"kind":"obs","gen":1,"seq":1,"target":"A","value":True}],
}
POLICIES=("RESIDENT_INCREMENTAL","LAST_MESSAGE","MESSAGE_COUNT","RESTART_REPLAY_UNGUARDED")

def apply(policy, events):
    actions=[]; gen=1; target="A"; lastseq={}; prev=False; revoked=False
    for i,e in enumerate(events):
        if policy=="RESIDENT_INCREMENTAL":
            if e["kind"]=="restart": gen=e["gen"]; lastseq={}; prev=False; revoked=False
            elif e["kind"]=="replace": gen=e["gen"]; target=e["target"]; prev=False; revoked=False
            elif e["kind"]=="revoke":
                if e["gen"]==gen and e["target"]==target: revoked=True; prev=False
            elif e["kind"]=="obs":
                if e["gen"]==gen and e["target"]==target and e["seq"]>lastseq.get(e["gen"],-1):
                    lastseq[e["gen"]]=e["seq"]
                    if not revoked and e["value"] and not prev: actions.append(i)
                    prev=bool(e["value"])
        elif policy=="LAST_MESSAGE":
            pass
        elif policy=="MESSAGE_COUNT":
            if e["kind"]=="obs" and e["value"]: actions.append(i)
        else:
            if e["kind"]=="obs" and e["value"]: actions.append(i)
    if policy=="LAST_MESSAGE" and events and events[-1]["kind"]=="obs" and events[-1].get("value"): actions=[len(events)-1]
    return actions

def find_window(root):
    for _ in range(150):
        for w in root.query_tree().children:
            try:
                if (w.get_wm_name() or "").startswith("resident-fixture:"): return w
            except Exception: pass
        time.sleep(.02)
    raise RuntimeError("fixture window missing")

def run_row(policy, case, events, effect):
    display_name=":202"; env={**os.environ,"DISPLAY":display_name,"EFFECT_MODE":"on" if effect else "off"}
    xvfb=subprocess.Popen(["/usr/bin/Xvfb",display_name,"-screen","0","640x480x24","-nolisten","tcp"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    app=None; conn=None
    try:
        time.sleep(.12); conn=display.Display(display_name); root=conn.screen().root
        app=subprocess.Popen(["python3","/src/fixture.py"],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        w=find_window(root); w.set_input_focus(X.RevertToParent,X.CurrentTime); conn.sync()
        before=root.get_image(0,0,640,480,X.ZPixmap,0xFFFFFFFF).data
        action_ix=apply(policy,events)
        code=conn.keysym_to_keycode(0x20)
        for _ in action_ix:
            xtest.fake_input(conn,X.KeyPress,code); conn.sync(); xtest.fake_input(conn,X.KeyRelease,code); conn.sync()
        deadline=time.monotonic()+1.5; expected=f"resident-fixture:{len(action_ix) if effect else 0}"
        while w.get_wm_name()!=expected and time.monotonic()<deadline: time.sleep(.01)
        after=root.get_image(0,0,640,480,X.ZPixmap,0xFFFFFFFF).data
        keymap=conn.query_keymap(); released=not bool(keymap[code//8]&(1<<(code%8)))
        return {"policy":policy,"case":case,"events":events,"action_event_indices":action_ix,"transport_count":len(action_ix),"effect_enabled":effect,"gui_title":w.get_wm_name(),"task_effect_count":int(w.get_wm_name().split(":")[-1]),"screen_before_sha256":hashlib.sha256(before).hexdigest(),"screen_after_sha256":hashlib.sha256(after).hexdigest(),"screen_changed":before!=after,"key_release_verified":released}
    finally:
        if conn: conn.close()
        if app:
            app.terminate(); app.wait(timeout=3)
        xvfb.terminate(); xvfb.wait(timeout=3)

def main():
    rows=[]
    for case,events in CASES.items():
        for policy in POLICIES:
            rows.append(run_row(policy,case,events,case!="effect_off"))
    out=Path("/evidence"); out.mkdir(parents=True,exist_ok=True)
    (out/"rows.json").write_text(json.dumps(rows,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"allocation":"issue3518-resident-gtk-incremental-01","rows":len(rows),"all_released":all(r["key_release_verified"] for r in rows),"gui_effect_rows":sum(r["screen_changed"] for r in rows)},sort_keys=True))
    if len(rows)!=32 or not all(r["key_release_verified"] for r in rows): raise SystemExit(2)

if __name__=="__main__": main()
