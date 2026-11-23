"""Run one current-main Linux MCP contract bundle normally and with -O."""
from __future__ import annotations
import hashlib,json,subprocess,sys,time
from pathlib import Path
PACKET=Path(__file__).resolve().parent

def repo_root():
    for p in (PACKET,*PACKET.parents):
        if (p/".git").exists(): return p
    raise RuntimeError("repository root not found")
REPO=repo_root()
CONDITIONS=PACKET/"CONDITIONS-r04.json"
RAW=PACKET/"raw-r04"
IMAGE="sha256:a3b2b4cd54ca731a86f8d2ba16f1eb833220122c60bfafbdb048e5ad39e50056"
MODULES=["runtime.cli_v1.test_mcp_server","runtime.cli_v1.test_mcp_guarded"]
def run(args,**kwargs): return subprocess.run(args,cwd=REPO,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False,**kwargs)
def sha(b): return hashlib.sha256(b).hexdigest()
def main():
    c=json.loads(CONDITIONS.read_text(encoding="utf-8"))
    base=subprocess.check_output(["git","rev-parse","origin/main"],cwd=REPO,text=True).strip()
    if base!=c["base_main_sha"]: raise SystemExit("origin/main moved from frozen base")
    for n,h in c["source_sha256"].items():
        if sha((REPO/n).read_bytes())!=h: raise SystemExit(f"source drift: {n}")
    image=subprocess.check_output(["docker","image","inspect",IMAGE,"--format","{{.Id}}"],text=True).strip()
    if image!=c["design"]["image_id"]: raise SystemExit("Docker image ID mismatch")
    if RAW.exists(): raise SystemExit("raw output exists; refusing overwrite")
    RAW.mkdir()
    mount=f"type=bind,source={REPO},target=/workspace,readonly"
    prefix=["docker","run","--rm","--network","none","--mount",mount,"--workdir","/workspace","--env","PYTHONPATH=/workspace",IMAGE]
    pre=run(prefix+["python3","--version"])
    (RAW/"preflight.stdout.bin").write_bytes(pre.stdout); (RAW/"preflight.stderr.bin").write_bytes(pre.stderr)
    (RAW/"preflight.exitcode.txt").write_text(f"{pre.returncode}\n",encoding="ascii")
    if pre.returncode: raise SystemExit("Python preflight failed; suite not launched")
    results=[]
    for mode,flags in (("normal",[]),("optimized",["-O"])):
        cmd=prefix+["python3","-B",*flags,"-m","unittest","-v",*MODULES]
        start=time.perf_counter_ns(); p=run(cmd); elapsed=time.perf_counter_ns()-start
        (RAW/f"{mode}.stdout.bin").write_bytes(p.stdout); (RAW/f"{mode}.stderr.bin").write_bytes(p.stderr)
        (RAW/f"{mode}.exitcode.txt").write_text(f"{p.returncode}\n",encoding="ascii")
        results.append({"mode":mode,"command":cmd,"returncode":p.returncode,"elapsed_ns":elapsed,"stdout_sha256":sha(p.stdout),"stderr_sha256":sha(p.stderr),"stdout_bytes":len(p.stdout),"stderr_bytes":len(p.stderr)})
    receipt={"schema":"issue57-current-main-docker-mcp-linux-r02","base_main_sha":base,"image_id":image,"python_preflight":pre.stdout.decode("utf-8","replace").strip(),"network":"none","source_mount":"read-only","runs":results}
    (PACKET/"run_results.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8",newline="")
    print(json.dumps(receipt,sort_keys=True))
    return 0
if __name__=="__main__": raise SystemExit(main())
