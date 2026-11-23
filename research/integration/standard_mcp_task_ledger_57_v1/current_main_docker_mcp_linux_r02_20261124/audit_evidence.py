"""Audit frozen source, exact Docker outputs and unittest outcomes."""
import hashlib,json,subprocess
from pathlib import Path
PACKET=Path(__file__).resolve().parent
for candidate in (PACKET,*PACKET.parents):
    if (candidate/".git").exists(): REPO=candidate; break
else: raise RuntimeError("repository root not found")
def sha(b): return hashlib.sha256(b).hexdigest()
def require(ok,msg):
    if not ok: raise AssertionError(msg)
def main():
    c=json.loads((PACKET/"CONDITIONS-r07.json").read_text(encoding="utf-8"))
    require(subprocess.check_output(["git","rev-parse","origin/main"],cwd=REPO,text=True).strip()==c["base_main_sha"],"main drift")
    source={}
    for n,h in c["source_sha256"].items():
        actual=sha((REPO/n).read_bytes()); require(actual==h,"source hash mismatch: "+n); source[n]=actual
    rr=json.loads((PACKET/"run_results.json").read_text(encoding="utf-8"))
    require(rr["base_main_sha"]==c["base_main_sha"] and rr["image_id"]==c["design"]["image_id"],"run provenance mismatch")
    preout=(PACKET/"raw-r04/preflight.stdout.bin").read_bytes(); preerr=(PACKET/"raw-r04/preflight.stderr.bin").read_bytes()
    require((PACKET/"raw-r04/preflight.exitcode.txt").read_text().strip()=="0","preflight exit not zero")
    require(b"3.11.2" in preout+preerr,"container Python version differs")
    rows=rr["runs"]; require([x["mode"] for x in rows]==["normal","optimized"],"run set differs")
    audits=[]
    for x in rows:
        mode=x["mode"]; out=(PACKET/f"raw-r04/{mode}.stdout.bin").read_bytes(); err=(PACKET/f"raw-r04/{mode}.stderr.bin").read_bytes()
        require(sha(out)==x["stdout_sha256"] and sha(err)==x["stderr_sha256"],mode+" raw hash mismatch")
        ec=(PACKET/f"raw-r04/{mode}.exitcode.txt").read_text().strip(); require(ec==str(x["returncode"]),mode+" exit mismatch")
        combined=out+err
        require(b"Ran 87 tests" in combined,mode+" test count missing")
        failed=(x["returncode"]!=0 or b"FAILED" in combined or b"OK" not in combined)
        audits.append({"mode":mode,"exit":x["returncode"],"tests":87,"passed":not failed,"failure_signature_present":b"did not observe its dispatch worker" in combined,"elapsed_ns":x["elapsed_ns"],"stdout_sha256":sha(out),"stderr_sha256":sha(err)})
    status="PASS_CURRENT_MAIN_BOTH_MODES" if all(x["passed"] for x in audits) else "HOLD_FAILURE_RETAINED"
    result={"schema":"issue57-current-main-docker-mcp-linux-r02-audit","status":status,"base_main_sha":c["base_main_sha"],"image_id":c["design"]["image_id"],"container_python":"3.11.2","network":"none","source_hashes_verified":source,"runs":audits,"limits":["No live GUI, model/provider, external allocation, WSLc, task effect, or recovery behavior was exercised.","This verifies only the Linux public-MCP test bundle under the frozen cached image.","The normal/-O outcomes characterize current-main tests; they do not estimate product reliability or efficiency."]}
    (PACKET/"AUDIT.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8",newline="")
    print(json.dumps(result,sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
