from __future__ import annotations
import hashlib, json, time
from pathlib import Path
from compiler import compile_literal, compile_guarded, evaluate_literal, evaluate_guarded, validate_guarded_artifact

ROOT=Path(__file__).resolve().parents[1]

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    out=ROOT/"results/formal_rows.json"
    marker=ROOT/"results/FORMAL_INVOKED.json"
    if out.exists() or marker.exists(): raise SystemExit("formal rerun forbidden")
    freeze=json.loads((ROOT/"FREEZE.json").read_text())
    for rel,h in freeze["source_sha256"].items():
        if sha(ROOT/rel)!=h: raise SystemExit(f"source drift {rel}")
    if sha(ROOT/"fixture.json")!=freeze["fixture_sha256"]: raise SystemExit("fixture drift")
    marker.write_text(json.dumps({"formal_invocation":1,"reruns":0},sort_keys=True)+"\n")
    fx=json.loads((ROOT/"fixture.json").read_text())
    literal=compile_literal(fx["compile_example"])
    guarded=compile_guarded(fx["compile_example"])
    validate_guarded_artifact(guarded, forbidden_token=fx["compile_example"]["token"])
    rows=[]
    for st in fx["states"]:
        for name,artifact,func in [("LITERAL_REPLAY",literal,evaluate_literal),("GUARDED_TYPED_MACRO",guarded,evaluate_guarded)]:
            t0=time.perf_counter_ns(); r=func(artifact,st); elapsed=time.perf_counter_ns()-t0
            rows.append({"state_id":st["state_id"],"task_id":st["task_id"],"layout":st["layout"],"artifact":name,"decision_ns":elapsed,**r})
    out.write_text(json.dumps(rows,indent=2,sort_keys=True)+"\n")
    result={"task":"CHROMIUM-PROCEDURE-GUARDED-MACRO-20260917-001","formal_invocations":1,"reruns":0,"rows":len(rows),"literal_artifact":literal,"guarded_artifact":guarded,"formal_rows_sha256":sha(out)}
    (ROOT/"results/RUNNER_RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"rows":len(rows),"sha256":sha(out)},sort_keys=True))
if __name__=="__main__": main()
