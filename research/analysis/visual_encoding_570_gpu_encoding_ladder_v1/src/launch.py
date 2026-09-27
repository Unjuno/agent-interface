from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys, time
from pathlib import Path

OLLAMA_IMAGE="sha256:8262851b2846b87c649eddf3e76beb270c52f4d1bc94559f47efde16b0841551"
HELPER_IMAGE="sha256:570ad778e44baf0bd094241515ed6cbbc7ce154321a7d76f295c42f2d5799261"
MODEL_DIGEST="fb90415cde1ef08aa669ae74b082d49b158729b6db1ab183c941417d507e71a1"
CONTAINER="agent-interface-570-r5-grid-context-ollama"
NETWORK="agent-interface-570-r5-grid-context-internal"
def run(cmd,check=True,capture=False,**kw):
    cp=subprocess.run(cmd,text=True,capture_output=capture,timeout=kw.get("timeout",600))
    if check and cp.returncode: raise RuntimeError(f"command exit {cp.returncode}: {cmd[:5]} stderr={cp.stderr if capture else ''}")
    return cp
def docker_missing(kind,name):
    cp=run(["docker",kind,"inspect",name],False,True)
    if cp.returncode==0: raise SystemExit(f"STOP name already exists; refusing to adopt {kind} {name}")
    if "No such" not in cp.stderr and "not found" not in cp.stderr.lower(): raise SystemExit("STOP cannot verify unique Docker name")
def helper(root,evidence,network,script,*args,network_none=False):
    net="none" if network_none else network
    return run(["docker","run","--rm","--platform","linux/amd64","--network",net,"--cpus","2","--memory","4g","--pids-limit","64",
      "--mount",f"type=bind,source={root},target=/src,readonly","--mount",f"type=bind,source={evidence},target=/out",
      "--mount",f"type=bind,source={evidence/'data'},target=/data,readonly","--entrypoint","python",HELPER_IMAGE,f"/src/{script}",*args],False,True)
def main():
    p=argparse.ArgumentParser(); p.add_argument("--root",type=Path,required=True); p.add_argument("--evidence",type=Path,required=True); p.add_argument("--model-store",type=Path,required=True); a=p.parse_args()
    root=a.root.resolve(); ev=a.evidence.resolve(); store=a.model_store.resolve(); freeze=json.loads((root/"FREEZE.json").read_text(encoding="utf-8"))
    for name,digest in freeze["source_sha256"].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest: raise SystemExit("STOP frozen source mismatch: "+name)
    if not (ev/"data"/"PREFORMAL.json").is_file(): raise SystemExit("STOP PREFORMAL missing")
    pre=json.loads((ev/"data"/"PREFORMAL.json").read_text(encoding="utf-8"))
    if len(pre["formal_cases"])!=60 or (ev/"baseline.json").exists() or (ev/"formal").exists(): raise SystemExit("STOP invalid denominator or prior formal evidence")
    docker_missing("network",NETWORK); docker_missing("container",CONTAINER)
    ev.mkdir(parents=True,exist_ok=True); run(["docker","network","create","--internal",NETWORK])
    (ev/"commands.json").write_text(json.dumps({"allocation":pre["allocation"],"network":["docker","network","create","--internal",NETWORK],"ollama":["docker","run","-d","--platform","linux/amd64","--network",NETWORK,"--network-alias","ollama","--gpus","all","--mount","<MODEL_STORE>:/models:ro","--env","OLLAMA_NO_CLOUD=true",OLLAMA_IMAGE,"serve"],"formal":"60 sequential calls, no retry","audit":"pinned helper image, --network none, separate process"},indent=2)+"\n",encoding="utf-8")
    run(["docker","run","-d","--name",CONTAINER,"--platform","linux/amd64","--network",NETWORK,"--network-alias","ollama","--gpus","all","--mount",f"type=bind,source={store},target=/models,readonly","--env","OLLAMA_MODELS=/models","--env","OLLAMA_NO_CLOUD=true","--env","OLLAMA_NUM_PARALLEL=1",OLLAMA_IMAGE,"serve"])
    sampler=None
    try:
        deadline=time.monotonic()+90
        while time.monotonic()<deadline:
            if run(["docker","exec",CONTAINER,"ollama","list"],False,True).returncode==0: break
            time.sleep(1)
        else: raise SystemExit("STOP Ollama readiness timeout; no request")
        ident=helper(root,ev,NETWORK,"model_runner.py","--mode","identity")
        (ev/"identity.stdout.txt").write_text(ident.stdout,encoding="utf-8"); (ev/"identity.stderr.txt").write_text(ident.stderr,encoding="utf-8")
        if ident.returncode: raise SystemExit("STOP cached model digest mismatch; no formal request")
        base=run(["nvidia-smi","--query-gpu=memory.used,utilization.gpu","--format=csv,noheader,nounits"],True,True)
        ps=run(["docker","exec",CONTAINER,"ollama","ps"],True,True)
        used,util=[int(x.strip()) for x in base.stdout.strip().splitlines()[0].split(",")]
        if len(ps.stdout.strip().splitlines())>1: raise SystemExit("STOP server is not empty at baseline")
        (ev/"baseline.json").write_text(json.dumps({"memory_used_mib":used,"gpu_utilization_percent":util,"nvidia_smi_raw":base.stdout,"ollama_ps_raw":ps.stdout,"baseline_is_empty_server":True},indent=2)+"\n",encoding="utf-8")
        (ev/"ollama-start.log").write_text(run(["docker","logs",CONTAINER],True,True).stdout,encoding="utf-8")
        sampler=subprocess.Popen([sys.executable,str(root/"sampler.py"),"--container",CONTAINER,"--out",str(ev/"sampler.jsonl"),"--stop-file",str(ev/"STOP_SAMPLER")])
        time.sleep(1)
        formal=helper(root,ev,NETWORK,"model_runner.py","--mode","formal")
        (ev/"formal.stdout.txt").write_text(formal.stdout,encoding="utf-8"); (ev/"formal.stderr.txt").write_text(formal.stderr,encoding="utf-8")
        (ev/"STOP_SAMPLER").write_text("formal block complete\n",encoding="utf-8"); sampler.wait(timeout=20); sampler=None
        (ev/"ollama-final.log").write_text(run(["docker","logs",CONTAINER],False,True).stdout,encoding="utf-8")
        out=ev/"audit"; out.mkdir(exist_ok=False)
        aud=run(["docker","run","--rm","--platform","linux/amd64","--network","none","--cpus","1","--memory","2g","--pids-limit","32","--mount",f"type=bind,source={root},target=/src,readonly","--mount",f"type=bind,source={ev},target=/evidence,readonly","--mount",f"type=bind,source={out},target=/out","--entrypoint","python",HELPER_IMAGE,"/src/audit.py","--root","/evidence","--out","/out/AUDIT.json"],False,True)
        (out/"stdout.txt").write_text(aud.stdout,encoding="utf-8"); (out/"stderr.txt").write_text(aud.stderr,encoding="utf-8")
        if formal.returncode: raise SystemExit("HOLD first formal request failure retained, no retry")
        if aud.returncode: raise SystemExit("HOLD independent auditor failed; raw evidence retained")
        print((out/"AUDIT.json").read_text(encoding="utf-8"))
    finally:
        if sampler is not None:
            (ev/"STOP_SAMPLER").write_text("launcher exit\n",encoding="utf-8")
            try: sampler.wait(timeout=10)
            except subprocess.TimeoutExpired: sampler.kill()
        run(["docker","stop",CONTAINER],False,True)
        run(["docker","network","rm",NETWORK],False,True)
if __name__=="__main__": main()
