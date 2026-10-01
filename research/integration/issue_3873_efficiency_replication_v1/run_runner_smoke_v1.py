"""One fake-response no-image runner smoke with the exact nested image command."""
from __future__ import annotations
import hashlib,json,subprocess,threading,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=HERE/"evidence/runner-smoke-v1"
IMAGE="sha256:5cc4d237e6af4548147ddfffc35413faf2487fd585f6a0216221f153f61cf073"

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    if OUT.exists():raise SystemExit("STOP_SMOKE_OUTPUT_EXISTS")
    OUT.mkdir(parents=True)
    case=OUT/"run-01"; case.mkdir()
    ipc=case/"ipc"; ipc.mkdir(); repo=case/"repo"; repo.mkdir(); work=repo/"workspace";work.mkdir()
    output=case/"output"; prompt=case/"prompt.txt";prompt.write_text("Return valid JSON for the requested schema.")
    schema=ROOT/"research/live_control/plain_form_points_schema_v1.json"
    instructions=ROOT/"research/live_control/schema_preflight_responder_v1.txt"
    (repo/"schema.json").write_bytes(schema.read_bytes());(repo/"instructions.txt").write_bytes(instructions.read_bytes())
    value={"format":"plain-form-points-v1","field":{"point_space":"source_observation_pixels","point":{"x":400,"y":300}},"submit":{"point_space":"source_observation_pixels","point":{"x":900,"y":700}}}
    events=(json.dumps({"type":"thread.started","thread_id":"fake-smoke-284937"})+"\n"+
        json.dumps({"type":"item.completed","item":{"type":"error","message":"synthetic auxiliary"}})+"\n"+
        json.dumps({"type":"item.completed","item":{"type":"agent_message","text":json.dumps(value,separators=(",",":"))}})+"\n"+
        json.dumps({"type":"turn.completed","usage":{"input_tokens":3,"cached_input_tokens":0,"cache_write_input_tokens":0,"output_tokens":4,"reasoning_output_tokens":0}})+"\n").encode()
    (case/"fake-events.jsonl").write_bytes(events)
    fake={"error":None}
    def responder():
        deadline=time.monotonic()+20
        try:
            reqs=[]
            while time.monotonic()<deadline:
                reqs=list(ipc.glob("*.request.json"))
                if reqs:break
                time.sleep(.02)
            if len(reqs)!=1:raise RuntimeError("fake request count:"+str(len(reqs)))
            req=json.loads(reqs[0].read_text())
            if req.get("mode")!="handle" or req.get("image") is not None or req.get("authority_granted") is not False:
                raise RuntimeError("fake smoke request contract mismatch")
            (ipc/(req["request_id"]+".response.jsonl")).write_bytes(events)
            (ipc/(req["request_id"]+".broker.json")).write_text(json.dumps({"host_cli_invoked":False,"returncode":0,"authority_granted":False})+"\n")
            fake.update({"request_id":req["request_id"],"fake_only":True,"host_cli_invoked":False})
        except Exception as e:fake["error"]=repr(e)
    thread=threading.Thread(target=responder,daemon=True);thread.start()
    command=["docker","--context","orbstack","run","--rm","--network","none",
        "-e","HOST_MODEL_IPC_DIR=/ipc","-v",f"{output}:/out","-v",f"{ipc}:/ipc",
        "-v",f"{HERE/'container_host_model_ipc_runner_v3.py'}:/repo/runner.py:ro",
        "-v",f"{instructions}:/repo/instructions.txt:ro","-v",f"{prompt}:/repo/prompt.txt:ro",
        "-v",f"{schema}:/repo/schema.json:ro","-v",f"{work}:/repo/workspace",
        IMAGE,"python","/repo/runner.py","/usr/bin/node","/usr/bin/true","/repo/prompt.txt",
        "/repo/workspace","/out/run","handle","-","/repo/instructions.txt","/repo/schema.json"]
    try:completed=subprocess.run(command,capture_output=True,text=True,timeout=35)
    except subprocess.TimeoutExpired:
        (case/"timeout.json").write_text(json.dumps({"status":"STOP_TIMEOUT_NO_HOST_CALL","retry":False},indent=2)+"\n")
        raise SystemExit("STOP_RUNNER_SMOKE_TIMEOUT")
    thread.join(timeout=2)
    for n,v in (("container.stdout.txt",completed.stdout),("container.stderr.txt",completed.stderr)):(case/n).write_text(v)
    (case/"command.json").write_text(json.dumps(command,indent=2)+"\n")
    (case/"fake-receipt.json").write_text(json.dumps(fake,indent=2)+"\n")
    if fake["error"] or completed.returncode!=0:raise SystemExit("FAIL_RUNNER_SMOKE:"+str(fake["error"])+":"+str(completed.returncode))
    print(json.dumps({"status":"RUNNER_COMMAND_SMOKE_RETURNED","runner_image":IMAGE,"returncode":completed.returncode,"fake_host_cli_calls":0}))
if __name__=="__main__":main()
