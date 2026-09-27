from __future__ import annotations
import json,sys
import formal

def main(path):
    retained=json.load(open(path))
    recomputed=formal.compute()
    errors=[]
    for k in ("candidate_oracle_mismatch","fixed_controls_pass","fixed_controls_total","role_counts","row_digest_sha256"):
        if retained.get(k)!=recomputed.get(k): errors.append("mismatch:"+k)
    if retained.get("seed")!=formal.SEED or retained.get("rows")!=formal.N: errors.append("schedule")
    if retained.get("formal_invocations")!=1 or retained.get("reruns")!=0 or retained.get("replacements")!=0 or retained.get("tuning")!=0: errors.append("discipline")
    if retained.get("decision")!="PASS_MAP01_TASK_EFFECT_INSTRUMENTATION_CONTRACT_SCOPED": errors.append("decision")
    out={"schema":"map01-task-effect-contract-audit-v1","pass":not errors,"errors":errors,"recomputed_digest":recomputed["row_digest_sha256"],"audit_invocations":1,"formal_invocations_added_by_audit":0}
    print(json.dumps(out,sort_keys=True,indent=2))
    return 0 if not errors else 1
if __name__=="__main__":
    if len(sys.argv)!=2: raise SystemExit("usage: audit.py FORMAL_RESULT.json")
    raise SystemExit(main(sys.argv[1]))
