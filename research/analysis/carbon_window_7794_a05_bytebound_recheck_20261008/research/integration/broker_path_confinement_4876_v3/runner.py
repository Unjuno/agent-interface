from __future__ import annotations
import importlib.util, json, os, tempfile, time
from pathlib import Path
from unittest.mock import patch
from path_policy import resolve_host_path

ROOT = Path(__file__).resolve().parent
BROKER_FILE = ROOT / "broker_under_test.py"

def load_broker():
    spec = importlib.util.spec_from_file_location("broker_under_test", BROKER_FILE)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

def main(outdir: Path) -> int:
    outdir.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix="path4876-") as tmp:
        base=Path(tmp); repo=base/"repo"; outside=base/"outside"; ipc=base/"ipc"
        repo.mkdir(); outside.mkdir(); ipc.mkdir()
        (repo/"schema.json").write_text('{"type":"object"}',encoding="utf-8")
        (repo/"image.png").write_bytes(b"PNG-fixture")
        (outside/"secret").write_text("sentinel",encoding="utf-8")
        (repo/"work").mkdir()
        (repo/"in-link").symlink_to(repo/"schema.json")
        (repo/"out-link").symlink_to(outside/"secret")
        checks=[]
        def check(name,value,expected,accepted):
            try:
                actual=resolve_host_path(value,repo)
                ok=accepted and actual==expected
                reason=None
            except (ValueError,OSError) as e:
                actual=None; reason=type(e).__name__; ok=not accepted
            checks.append({"name":name,"input":value,"accepted":accepted,"actual":actual,"reason":reason,"pass":ok})
        check("repo-alias","/repo/schema.json",str((repo/"schema.json").resolve()),True)
        check("workspace-alias","/workspace/work",str((repo/"work").resolve()),True)
        check("root-alias","/repo",str(repo.resolve()),True)
        check("in-root-symlink","/repo/in-link",str((repo/"schema.json").resolve()),True)
        check("absolute-host",str(outside/"secret"),None,False)
        check("parent-traversal","/repo/../outside/secret",None,False)
        check("encoded-traversal","/repo/%252e%252e/outside/secret",None,False)
        check("backslash-traversal",r"/repo/..\\outside\\secret",None,False)
        check("external-symlink","/repo/out-link",None,False)
        check("missing","/repo/missing.json",None,False)
        broker=load_broker(); broker.host_path=lambda value,root: resolve_host_path(value,root)
        seen=[]
        class Completed:
            returncode=0; stderr=""; stdout='{"ok":true}\n'
        def recorder(args,**kwargs):
            seen.append({"args":args,"kwargs":{k:v for k,v in kwargs.items() if k!="input"}})
            return Completed()
        request={"request_id":"valid-01","schema":"/repo/schema.json","image":"/repo/image.png","working":"/workspace/work","prompt":"fixture"}
        (ipc/"valid-01.request.json").write_text(json.dumps(request),encoding="utf-8")
        with patch.object(broker.subprocess,"run",recorder):
            rc=broker.serve(ipc,repo,once=True)
        response=(ipc/"valid-01.response.jsonl").read_text(encoding="utf-8")
        broker_row=json.loads((ipc/"valid-01.broker.json").read_text(encoding="utf-8"))
        result={"allocation":"broker-path-confinement-4876-20260927-03","source_blob":"5734f54f318db9ac5e96b2bed6f6bed105ac39ff",
          "case_count":len(checks),"cases":checks,"all_path_checks_pass":all(x["pass"] for x in checks),
          "serve_valid_rc":rc,"subprocess_calls":len(seen),"valid_broker_returncode":broker_row.get("returncode"),
          "valid_mapped_paths":[seen[0]["args"][seen[0]["args"].index("--output-schema")+1],seen[0]["args"][-2]],
          "response":response,"authority_granted":broker_row.get("authority_granted"),
          "decision":"PASS_PATH_RESOLVER_CONSTRUCTION_SCOPED" if all(x["pass"] for x in checks) and len(seen)==1 and broker_row.get("returncode")==0 else "FAIL_PATH_RESOLVER"}
        (outdir/"RAW.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        print(json.dumps(result,sort_keys=True))
        return 0 if result["decision"].startswith("PASS") else 1
if __name__=="__main__":
 import sys
 raise SystemExit(main(Path(sys.argv[1])))





