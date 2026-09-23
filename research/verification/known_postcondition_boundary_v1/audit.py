from __future__ import annotations
import argparse,json
from pathlib import Path
TYPES=("file_digest","window_geometry","typed_state")
SCENARIOS=("valid","no_effect","stale","wrong_target","partial","ambiguous","missing_receipt","malformed","pixel_only","cleanup_failure")
def expected(row):
    s=row["scenario"]; v=row["verifier"]["verdict"]
    if s=="valid": return v=="PASS_POSTCONDITION"
    return v!="PASS_POSTCONDITION"
def main():
    ap=argparse.ArgumentParser();ap.add_argument("root",type=Path);a=ap.parse_args();rows=json.loads((a.root/"raw.json").read_text()); errs=[]
    if len(rows)!=90: errs.append("expected_90_policy_rows")
    for r in rows:
      if r["kind"] not in TYPES or r["scenario"] not in SCENARIOS: errs.append("identity")
      if r["scenario"]=="valid" and r["verifier"]["verdict"]!="PASS_POSTCONDITION": errs.append("valid_not_pass")
      if r["scenario"]!="valid" and r["verifier"]["verdict"]=="PASS_POSTCONDITION": errs.append("false_success:"+r["scenario"])
      if r["scenario"]=="pixel_only" and r["verifier"]["verdict"]=="PASS_POSTCONDITION": errs.append("pixel_only_pass")
    by={p:sum(r["rich_agent_calls"] for r in rows if r["policy"]==p) for p in ("RICH_AGENT_FIRST","DETERMINISTIC_FIRST","DETERMINISTIC_ONLY_FOR_KNOWN")}
    out={"schema":"agent-interface/known-postcondition-boundary-audit-v1","status":"PASS_AUDIT" if not errs else "FAIL_AUDIT","errors":errs,"rows":len(rows),"rich_agent_calls":by,"scientific_decision":"PASS_DETERMINISTIC_POSTCONDITION_BOUNDARY_SCOPED" if not errs else "FAIL_FALSE_POSTCONDITION_SUCCESS"}
    (a.root/"audit.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps(out,indent=2));raise SystemExit(0 if not errs else 2)
if __name__=="__main__":main()
