from __future__ import annotations
import copy, hashlib, json, sys
GATES=("task_decision","model_effort","current_evidence","history_pre_compaction","compaction_boundary","prompt_capability","session_cache_policy","independent_oracle")
ALLOWED={"PASS","FAIL","UNKNOWN"}

def canonical(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()

def evaluate(ledger):
    errors=[]
    if ledger.get("schema")!="pgws-compaction-identifiability-ledger-v1": errors.append("schema")
    rows=ledger.get("rows",[])
    if len({r.get("family") for r in rows})<3: errors.append("families")
    admissible=[]
    for r in rows:
        g=r.get("gates",{})
        if tuple(g.keys())!=GATES: errors.append("gate_shape:"+str(r.get("id")))
        if any(v not in ALLOWED for v in g.values()): errors.append("gate_value:"+str(r.get("id")))
        if all(g.get(k)=="PASS" for k in GATES): admissible.append(r.get("id"))
        if not r.get("sources") or any(not s.get("path") or len(s.get("git_blob",""))!=40 for s in r.get("sources",[])): errors.append("sources:"+str(r.get("id")))
        if not r.get("factor") or not r.get("evidence"): errors.append("explanation:"+str(r.get("id")))
    ex=ledger.get("excluded_prerequisites",[])
    if {x.get("issue") for x in ex}!={1560,1562}: errors.append("prerequisite_exclusion")
    result={
      "schema":"pgws-compaction-identifiability-result-v1",
      "task":ledger.get("task"),
      "families_inspected":len({r.get("family") for r in rows}),
      "candidate_rows":len(rows),
      "admissible_pair_ids":admissible,
      "admissible_pairs":len(admissible),
      "ledger_sha256":hashlib.sha256(canonical(ledger)).hexdigest(),
      "decision":"PASS_RETAINED_PGWS_COMPACTION_BENEFIT_IDENTIFIABLE_SCOPED" if admissible else "PASS_RETAINED_PGWS_COMPACTION_BENEFIT_NOT_IDENTIFIABLE_SCOPED",
      "errors":errors,
      "formal_invocations":1,
      "reruns":0,"replacements":0,"tuning":0
    }
    return result

def audit(ledger,result):
    exp=evaluate(ledger); errs=[]
    for k in ("task","families_inspected","candidate_rows","admissible_pair_ids","admissible_pairs","ledger_sha256","decision","formal_invocations","reruns","replacements","tuning"):
        if result.get(k)!=exp.get(k): errs.append(k)
    if exp["errors"]: errs.append("ledger_errors")
    return {"schema":"pgws-compaction-identifiability-audit-v1","pass":not errs,"errors":errs,"expected_admissible_pairs":exp["admissible_pairs"],"expected_decision":exp["decision"]}

if __name__=='__main__':
    ledger=json.load(open(sys.argv[1])); result=json.load(open(sys.argv[2])); out=audit(ledger,result); print(json.dumps(out,indent=2,sort_keys=True)); raise SystemExit(0 if out['pass'] else 3)
