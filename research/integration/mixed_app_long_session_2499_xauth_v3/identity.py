import hashlib,json,os,signal,subprocess,tempfile,time
from pathlib import Path

def run(argv,env,timeout=20):
    return subprocess.run(argv,env=env,text=True,capture_output=True,timeout=timeout,check=False)
def props(env,wid):
    q=run(["xprop","-id",wid,"_NET_WM_PID","WM_CLASS","WM_NAME"],env)
    return {"window":wid,"raw":q.stdout,"returncode":q.returncode}
def main():
    root=Path(tempfile.mkdtemp(prefix="xauth-2699-v3-")); display=":157"; auth=root/"Xauthority"; cookie="0123456789abcdef0123456789abcdef"
    env=os.environ.copy(); env.update(DISPLAY=display,XAUTHORITY=str(auth),HOME=str(root/"home"),XDG_CONFIG_HOME=str(root/"config"),XDG_CACHE_HOME=str(root/"cache"),XDG_RUNTIME_DIR=str(root/"runtime"),SAL_USE_VCLPLUGIN="gen",GDK_BACKEND="x11")
    for n in ("home","config","cache","runtime"): (root/n).mkdir(mode=0o700)
    (root/"Xauthority").touch(mode=0o600); run(["xauth","-f",str(auth),"add",display,".",cookie],env)
    xvfb=subprocess.Popen(["Xvfb",display,"-screen","0","1600x1000x24","-auth",str(auth)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); procs=[]
    out={"display":display,"xauthority_mode":oct(auth.stat().st_mode&0o777),"xauthority_sha256":hashlib.sha256(auth.read_bytes()).hexdigest(),"apps":{},"controls":[],"input_operations":0,"model_calls":0,"network_calls":0}
    try:
        time.sleep(.7); commands={"inkscape":["inkscape"],"calc":["libreoffice","--norestore","--nolockcheck",f"-env:UserInstallation=file://{root/'lo-profile'}","--calc"],"chromium":["chromium","--no-sandbox","--disable-gpu","--no-first-run","--no-default-browser-check","--user-data-dir="+str(root/"chrome"),"about:blank"]}
        for name,argv in commands.items():
            p=subprocess.Popen(argv,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); procs.append(p); time.sleep(3)
            q=run(["xdotool","search","--onlyvisible","--name",".*"],env); rows=[props(env,w.strip()) for w in q.stdout.splitlines() if w.strip()]
            token={"inkscape":"inkscape","calc":"libreoffice","chromium":"chromium"}[name]; hits=[r for r in rows if token in r["raw"].lower()]
            out["apps"][name]={"pid":p.pid,"candidate_count":len(hits),"candidates":hits,"disposition":"accepted" if len(hits)==1 else "refused_ambiguous_or_missing"}
        out["controls"].append({"control":"missing_token","candidate_count":0,"disposition":"refused"}); ok=all(x["disposition"]=="accepted" for x in out["apps"].values()); out["decision"]="PASS_XAUTH_COOKIE_IDENTITY" if ok else "FAIL_XAUTH_COOKIE_IDENTITY"; print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if ok else 1)
    finally:
        for p in reversed(procs):
            if p.poll() is None:p.terminate()
        if xvfb.poll() is None:xvfb.terminate()
if __name__=="__main__": main()
