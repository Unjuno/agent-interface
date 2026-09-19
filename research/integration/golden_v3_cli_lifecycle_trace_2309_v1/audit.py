from __future__ import annotations
import argparse, hashlib, json, subprocess
from pathlib import Path
from adapter import execute, STATES

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]

def blob(path):
    return subprocess.check_output(["git","hash-object",str(REPO/path)],cwd=REPO,text=True).strip()

def main():
    p=argparse.ArgumentParser(); p.add_argument("--mode",required=True); a=p.parse_args()
    trace=json.loads((ROOT/"TRACE.json").read_text())
    manifest=json.loads((ROOT/"SOURCE_MANIFEST.json").read_text())
    assert [r["state"] for r in trace]==list(STATES)
    for s in manifest["sources"]:
        path=Path(s["path"]); assert (REPO/path).is_file()
        assert blob(path)==s["blob_sha"], s["path"]
    out=[execute(r) for r in trace]
    assert all(r["authority_granted"] is False for r in out)
    assert out[1]["status"]=="model_failed" and out[1]["usage_available"] is False
    assert out[5]["partial_effects"]==["save"] and out[5]["task_success"] is True
    assert out[7]["program_completed"] is True and out[7]["task_success"] is False
    assert out[9]["status"]=="runtime_failed" and out[9]["execution"]["emissions"]==2
    canonical=json.dumps({"mode":a.mode,"rows":out},sort_keys=True,separators=(",",":"))
    digest=hashlib.sha256(canonical.encode()).hexdigest()
    print(json.dumps({"decision":"PASS_GOLDEN_V3_CLI_LIFECYCLE_TRACE_SCOPED","mode":a.mode,"rows":len(out),"authority_grants":0,"digest":digest},sort_keys=True))

if __name__=="__main__": main()
