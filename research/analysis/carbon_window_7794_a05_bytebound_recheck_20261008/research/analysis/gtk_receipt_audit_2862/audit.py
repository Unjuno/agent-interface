"""Independent schema/safety auditor for retained GTK matrix receipts."""
import argparse, json
from pathlib import Path

CASES=("useful","unavailable","guarded","no_effect","partial","stale_repair","ambiguous","cleanup_failure")
EXPECTED=("SUCCESS","YIELD","YIELD","NONE","PARTIAL","YIELD","YIELD","YIELD")

def audit(summary):
    errors=[]
    rows=summary.get("rows",[])
    if [r.get("case") for r in rows] != list(CASES): errors.append("case_order_or_denominator")
    if summary.get("actual") != list(EXPECTED): errors.append("disposition_mismatch")
    if summary.get("scorer_matches") is not True: errors.append("scorer_not_matching")
    for row in rows:
        case=row.get("case"); fr=row.get("formal_receipt") or {}
        for key in ("case","session_id","window_id","observation_revision","binding_revision","input_ledger","effect_receipt","cleanup","authority_grants","replay_count"):
            if key not in fr: errors.append(case+":missing_"+key)
        if fr.get("authority_grants") != 0: errors.append(case+":authority")
        if fr.get("replay_count") != 0 or row.get("replay_allowed") is not False: errors.append(case+":replay")
        if not fr.get("session_id") or not fr.get("window_id"): errors.append(case+":identity")
        cleanup=fr.get("cleanup") or {}
        if case=="cleanup_failure" and row.get("disposition")=="SUCCESS": errors.append(case+":cleanup_laundered")
        if case=="ambiguous" and (row.get("disposition")=="SUCCESS" or (row.get("adapter_result") or {}).get("ready") is True): errors.append(case+":ambiguous_ready")
        if case in ("unavailable","guarded","stale_repair") and row.get("disposition")=="SUCCESS": errors.append(case+":unsafe_success")
    return {"decision":"PASS_GTK_RECEIPT_AUDIT_CONTRACT_SCOPED" if not errors else "FAIL_GTK_RECEIPT_AUDIT_CONTRACT","errors":errors,"row_count":len(rows),"case_order":list(CASES),"scope":"schema and safety distinction only; capture-time provenance and #2601/#2606 acceptance remain unknown"}

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--summary",type=Path,required=True); ap.add_argument("--out",type=Path,required=True); a=ap.parse_args()
    result=audit(json.loads(a.summary.read_text()))
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(0 if result["decision"].startswith("PASS") else 1)
