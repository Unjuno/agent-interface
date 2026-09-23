"""One frozen model-free resolver allocation for Issue #2664."""
import json, os, signal, subprocess, tempfile, time
from pathlib import Path

APPS = {"inkscape": "inkscape", "calc": "libreoffice", "chromium": "chromium"}

def run(argv, env, timeout=15):
    return subprocess.run(argv, env=env, text=True, capture_output=True,
                          timeout=timeout, check=False)

def props(env, wid):
    q = run(["xprop", "-id", wid, "_NET_WM_PID", "WM_CLASS", "WM_NAME"], env)
    return {"window": wid, "raw": q.stdout, "returncode": q.returncode}

def candidates(env):
    q = run(["xdotool", "search", "--onlyvisible", "--name", ".*"], env)
    return [props(env, w.strip()) for w in q.stdout.splitlines() if w.strip()]

def matching(rows, token):
    return [r for r in rows if token.lower() in r["raw"].lower()]

def main():
    root = Path(tempfile.mkdtemp(prefix="identity-2664-"))
    env = os.environ.copy(); env.update(DISPLAY=":142", XAUTHORITY=str(root/"Xauthority"))
    (root/"Xauthority").touch(mode=0o600)
    xvfb = subprocess.Popen(["Xvfb", env["DISPLAY"], "-screen", "0", "1600x1000x24", "-auth", env["XAUTHORITY"]], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    procs=[]; out={"display":env["DISPLAY"],"xauthority_mode":"0600","apps":{},"controls":[],"input_operations":0,"model_calls":0,"network_calls":0}
    try:
        time.sleep(.7)
        commands={
          "inkscape":["inkscape","--no-splash","--new"],
          "calc":["libreoffice","--norestore","--nodefault","--nolockcheck","--calc"],
          "chromium":["chromium","--no-sandbox","--disable-gpu","--user-data-dir="+str(root/"chrome"),"about:blank"]}
        for name, argv in commands.items():
            p=subprocess.Popen(argv,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); procs.append(p); time.sleep(2)
            rows=candidates(env); token=APPS[name]; hits=matching(rows,token)
            out["apps"][name]={"pid":p.pid,"candidate_count":len(hits),"candidates":hits,"disposition":"accepted" if len(hits)==1 else "refused_ambiguous_or_missing"}
        missing=matching(candidates(env),"definitely-not-an-app")
        out["controls"].append({"control":"missing_token","candidate_count":len(missing),"disposition":"refused" if not missing else "unexpected_accept"})
        accepted=all(v["disposition"]=="accepted" for v in out["apps"].values())
        controls=all(c["disposition"]=="refused" for c in out["controls"])
        out["decision"]="PASS_WINDOW_IDENTITY_RESOLVER" if accepted and controls else "FAIL_WINDOW_IDENTITY_RESOLVER"
        print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if out["decision"].startswith("PASS") else 1)
    finally:
        for p in reversed(procs):
            if p.poll() is None: p.terminate()
        if xvfb.poll() is None: xvfb.terminate()

if __name__ == "__main__": main()
