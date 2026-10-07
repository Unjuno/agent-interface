import datetime, json, os, pathlib, signal, subprocess, sys, time
root = pathlib.Path(__file__).resolve().parent
result = {"started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "platform": sys.platform, "python": sys.version, "steps": []}
child_pid = None
parent = None
try:
    parent_code = (
        "import json,subprocess,sys,time; "
        "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); "
        "print(json.dumps({'descendant_pid':p.pid}),flush=True); time.sleep(30)"
    )
    parent = subprocess.Popen([sys.executable, "-c", parent_code], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    line = parent.stdout.readline()
    child_pid = json.loads(line)["descendant_pid"]
    result["descendant_pid"] = child_pid
    result["alive_before_parent_terminate"] = True
    parent.terminate()
    parent.wait(timeout=3)
    time.sleep(0.25)
    try:
        os.kill(child_pid, 0)
        result["alive_after_parent_terminate"] = True
    except OSError:
        result["alive_after_parent_terminate"] = False
    result["parent_returncode"] = parent.returncode
    result["steps"].append({"step":"direct_parent_terminate_control","descendant_alive_after":result["alive_after_parent_terminate"],"parent_returncode":parent.returncode})
finally:
    if child_pid:
        try: os.kill(child_pid, signal.SIGTERM)
        except OSError: pass
    if parent:
        if parent.poll() is None:
            parent.kill(); parent.wait(timeout=3)
        for f in (parent.stdout,parent.stderr):
            if f and not f.closed: f.close()
    result["completed_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
(root / "control-result.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
print(json.dumps(result, indent=2))
