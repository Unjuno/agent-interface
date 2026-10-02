#!/usr/bin/env python3
"""Independent raw-only audit for the synthetic CUDA supervisor probe."""
import argparse, copy, hashlib, json, statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parent
THRESHOLD=700

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def oracle(row):
    hint=row["confidence_milli"] >= THRESHOLD
    eligible=(row["observed_sequence"]==row["current_sequence"] and
              row["ambiguous"] is False and row["forced_yield"] is False)
    return ("CONTINUE" if hint else "YIELD", int(hint and eligible))
def audit(result,doc,freeze):
    errors=[]
    if result.get("schema")!="gpu-supervisor-cuda-4972-result-v1": errors.append("schema")
    if result.get("allocation")!=freeze["allocation"]: errors.append("allocation")
    if result.get("base_main_sha")!=freeze["base_main_sha"]: errors.append("base_sha")
    if result.get("dataset_sha256")!=sha(ROOT/"dataset.json"): errors.append("dataset_sha")
    if result.get("source_sha256",{}).get("runner")!=freeze["runner_sha256"]: errors.append("runner_sha")
    rows=doc.get("rows",[]); got=result.get("rows",[])
    if len(rows)!=256 or len(got)!=len(rows): errors.append("row_count")
    for i,(r,o) in enumerate(zip(rows,got)):
        hint,admit=oracle(r)
        if o.get("id")!=r.get("id"): errors.append(f"id:{i}")
        if o.get("cpu_hint")!=hint: errors.append(f"cpu_oracle:{i}")
        if o.get("gpu_hint")!=hint: errors.append(f"gpu_oracle:{i}")
        if o.get("cpu_admitted")!=admit: errors.append(f"cpu_gate:{i}")
        if o.get("gpu_admitted")!=admit: errors.append(f"gpu_gate:{i}")
        if not (r["observed_sequence"]==r["current_sequence"]) and o.get("gpu_admitted"):
            errors.append(f"stale_admission:{i}")
        if (r["ambiguous"] or r["forced_yield"]) and o.get("gpu_admitted"):
            errors.append(f"blocked_admission:{i}")
    m=result.get("timing_diagnostic_only",{})
    for k in ("cpu_ns","gpu_ns"):
        vals=m.get(k,[])
        if len(vals)!=30 or any(not isinstance(x,int) or x<=0 for x in vals): errors.append("timing:"+k)
        elif m.get(k.replace("_ns","_p50_ns"))!=statistics.median(vals): errors.append("p50:"+k)
    controls={}
    bad=copy.deepcopy(result); bad["rows"][0]["gpu_hint"]="YIELD" if bad["rows"][0]["gpu_hint"]=="CONTINUE" else "CONTINUE"
    controls["hint_mutation_rejected"]=bool(audit_core_errors(bad,doc,freeze))
    bad=copy.deepcopy(result); stale=next((i for i,r in enumerate(doc["rows"]) if r["observed_sequence"]!=r["current_sequence"]),None)
    if stale is not None: bad["rows"][stale]["gpu_admitted"]=1
    controls["stale_admission_mutation_rejected"]=bool(audit_core_errors(bad,doc,freeze))
    bad=copy.deepcopy(result); bad["dataset_sha256"]="0"*64
    controls["dataset_hash_mutation_rejected"]=bool(audit_core_errors(bad,doc,freeze))
    if not all(controls.values()): errors.append("mutation_controls")
    return errors,controls
def audit_core_errors(result,doc,freeze):
    # Recompute core row integrity independently; timing and controls are checked by outer audit.
    errs=[]
    if result.get("dataset_sha256")!=sha(ROOT/"dataset.json"): errs.append("dataset_sha")
    if result.get("allocation")!=freeze["allocation"] or result.get("base_main_sha")!=freeze["base_main_sha"]: errs.append("identity")
    for i,(r,o) in enumerate(zip(doc.get("rows",[]),result.get("rows",[]))):
        h,a=oracle(r)
        if o.get("id")!=r.get("id") or o.get("cpu_hint")!=h or o.get("gpu_hint")!=h or o.get("cpu_admitted")!=a or o.get("gpu_admitted")!=a: errs.append(str(i))
    return errs
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--raw",default="candidate_result.json");ap.add_argument("--out",default="audit_result.json");a=ap.parse_args()
    freeze=json.loads((ROOT/"FREEZE.json").read_text()); doc=json.loads((ROOT/"dataset.json").read_text()); result=json.loads((ROOT/a.raw).read_text())
    if sha(Path(__file__))!=freeze["audit_sha256"]: raise RuntimeError("audit source freeze mismatch")
    errors,controls=audit(result,doc,freeze)
    out={"schema":"gpu-supervisor-cuda-4972-audit-v1","allocation":freeze["allocation"],"audit":"PASS" if not errors else "FAIL","errors":errors,"mutation_controls":controls,"raw_sha256":sha(ROOT/a.raw),"row_count":len(result.get("rows",[])),"cpu_gpu_exact_parity":not errors}
    (ROOT/a.out).write_text(json.dumps(out,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(out,sort_keys=True));raise SystemExit(0 if not errors else 1)
if __name__=="__main__":main()

