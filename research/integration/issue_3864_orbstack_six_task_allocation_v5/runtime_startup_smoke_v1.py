"""Start the exact checked fixture over its socket adapter without any model IPC."""
from __future__ import annotations
import hashlib,json,os,subprocess,sys,time
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
LIVE=ROOT/"research/live_control"
OUT=HERE/"evidence/runtime-startup-smoke-v2/run-01"
if OUT.exists():raise SystemExit("STOP_RUNTIME_SMOKE_OUTPUT_EXISTS")
OUT.mkdir(parents=True)
sys.path[:0]=[str(LIVE),str(HERE),str(ROOT),str(ROOT/"runtime")]
import integrated_efficiency_client_v1 as client_module
client_module.HERE=HERE
from integrated_efficiency_client_v1 import RuntimeClient

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

display=subprocess.Popen(["Xvfb",":99","-screen","0","1280x1024x24","-nolisten","tcp"],
    stdout=(OUT/"xvfb.stdout.txt").open("w"),stderr=(OUT/"xvfb.stderr.txt").open("w"))
client=RuntimeClient(OUT/"client",284936)
status="STOP_RUNTIME_STARTUP"
failure=None
evaluation=None
try:
    deadline=time.monotonic()+10
    while time.monotonic()<deadline:
        probe=subprocess.run(["xdpyinfo","-display",":99"],capture_output=True,text=True)
        if probe.returncode==0:break
        time.sleep(.1)
    else:raise RuntimeError("Xvfb display did not become ready")
    os.environ["DISPLAY"]=":99"
    os.environ["ISSUE3824_LIVE_SOURCE"]=str(LIVE)
    os.environ["ISSUE3824_REPO"]=str(ROOT)
    client.start()
    evaluation=client.finish("runtime-startup-smoke-finish")
    client.process.wait(timeout=10)
    client.close()
    if client.process.returncode!=0:raise RuntimeError("socket runtime exit:"+str(client.process.returncode))
    status="PASS_RUNTIME_STARTUP_NO_MODEL"
except Exception as exc:
    failure=repr(exc)
finally:
    try:client.close()
    except Exception as exc:failure=failure or repr(exc)
    display.terminate()
    try:display.wait(timeout=5)
    except subprocess.TimeoutExpired:display.kill();display.wait()
    stderr=client.errors
    if stderr is not None and not stderr.closed:stderr.close()

runtime_events=OUT/"client/runtime/events.jsonl"
result={"status":status,"failure":failure,"host_model_calls":0,
    "host_broker_model_calls":0,"runtime_exit_code":None if client.process is None else client.process.returncode,
    "fixture_clean_finish":evaluation is not None,"fixture_evaluation":evaluation,
    "runtime_events_sha256":sha(runtime_events) if runtime_events.exists() else None,
    "authority_granted":False,"network":"none","seed":284936}
(OUT/"runtime-startup-result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps(result,sort_keys=True))
if status!="PASS_RUNTIME_STARTUP_NO_MODEL":raise SystemExit("STOP_RUNTIME_STARTUP_NO_RETRY")
