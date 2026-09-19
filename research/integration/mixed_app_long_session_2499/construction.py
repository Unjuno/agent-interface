"""Model-free construction gate for the #2499 mixed-app session.
This only verifies coexistence and distinct visible windows owned by each launch's process tree.
"""
import json, os, signal, subprocess, tempfile, time
from pathlib import Path
APPS=("inkscape","libreoffice","chromium")
def run(cmd,env,timeout=20):
    return subprocess.run(cmd,env=env,text=True,capture_output=True,timeout=timeout,check=False)
def visible_windows(env):
    return [x for x in run(["xdotool","search","--onlyvisible","--name",".*"],env).stdout.splitlines() if x.strip()]
def process_tree(root_pid):
    rows=run(["ps","-eo","pid=,ppid="],os.environ).stdout.splitlines(); children={}
    for row in rows:
        f=row.split()
        if len(f)==2: children.setdefault(int(f[1]),[]).append(int(f[0]))
    seen={root_pid}; stack=[root_pid]
    while stack:
        p=stack.pop()
        for c in children.get(p,[]):
            if c not in seen: seen.add(c); stack.append(c)
    return seen
def owned_visible_windows(env,baseline,root_pid):
    owned=[]; pids=process_tree(root_pid)
    for w in visible_windows(env):
        if w in baseline: continue
        try: owner=int(run(["xdotool","getwindowpid",w],env).stdout.strip())
        except ValueError: continue
        if owner in pids: owned.append(w)
    return owned
def main():
    root=Path(tempfile.mkdtemp(prefix="mixed-2499-")); env=os.environ.copy()
    env.update(DISPLAY=":140",XAUTHORITY=str(root/"Xauthority"),HOME=str(root/"home"),XDG_CONFIG_HOME=str(root/"config"),XDG_CACHE_HOME=str(root/"cache"),XDG_RUNTIME_DIR=str(root/"runtime"),SAL_USE_VCLPLUGIN="gen",GDK_BACKEND="x11")
    for d in ("home","config","cache","runtime"): (root/d).mkdir(mode=0o700)
    (root/"Xauthority").touch(mode=0o600); procs=[]
    out={"apps":[],"input_operations":0,"model_calls":0,"network_calls":0,"display":env["DISPLAY"]}
    xvfb=subprocess.Popen(["Xvfb",env["DISPLAY"],"-screen","0","1600x1000x24","-auth",env["XAUTHORITY"]],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        time.sleep(.7)
        for app in APPS:
            if app=="inkscape": cmd=[app]
            elif app=="libreoffice": cmd=[app,"--norestore","--nolockcheck",f"-env:UserInstallation=file://{root/'lo-profile'}","--calc"]
            else: cmd=[app,"--no-sandbox","--disable-gpu","--no-first-run","--no-default-browser-check","--disable-session-crashed-bubble","--user-data-dir="+str(root/"chrome-profile"),"about:blank"]
            baseline=set(visible_windows(env)); p=subprocess.Popen(cmd,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); procs.append(p)
            deadline=time.monotonic()+15; owned=[]
            while time.monotonic()<deadline:
                owned=owned_visible_windows(env,baseline,p.pid)
                if owned: break
                time.sleep(.5)
            out["apps"].append({"app":app,"pid":p.pid,"window_count":len(owned),"windows":owned[:20],"observed":bool(owned),"owner_bound":bool(owned)})
        out["distinct_window_ids"]=len({w for x in out["apps"] for w in x["windows"]})==sum(x["window_count"] for x in out["apps"])
        out["owner_bound"]=all(x["owner_bound"] for x in out["apps"])
        out["decision"]="PASS_MIXED_APP_CONSTRUCTION_READY" if all(x["observed"] for x in out["apps"]) and out["distinct_window_ids"] and out["owner_bound"] else "HOLD_MIXED_APP_CONSTRUCTION"
        print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if out["decision"].startswith("PASS") else 1)
    finally:
        for p in reversed(procs):
            if p.poll() is None: p.send_signal(signal.SIGTERM)
        if xvfb.poll() is None: xvfb.send_signal(signal.SIGTERM)
if __name__=="__main__": main()
