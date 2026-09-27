"""Independent raw-only checker for Issue #4990 subprocess records."""
import hashlib
import json
import sys
from pathlib import Path

EXPECTED_DIGEST="c9e0871ce3272c99f91db2596fd02ffd3ba941ca10bf8a21662a45a5c302d68a"
EXPECTED={"SUCCEEDED":3,"BLOCKED":3,"AUTHORITY_REQUIRED":96,"TARGET_NOT_FOUND":6,"CAPABILITY_UNSUPPORTED":24,"CONFLICT":48,"IMPOSSIBLE_UNDER_CONSTRAINTS":12,"FAILED_UNKNOWN":192}
MODES=("normal","opt_flag","env_opt")

def check(condition,label,errors):
    if not condition: errors.append(label)

def audit(root):
    errors=[]
    for mode in MODES:
        raw=(root/(mode+".stdout")).read_bytes()
        receipt=json.loads(raw)
        check(receipt.get("decision")=="PASS_OPTIMIZATION_RESILIENT_CONTRACT_SCOPED",mode+":decision",errors)
        check(receipt.get("rows")==384,mode+":rows",errors)
        check(receipt.get("counts")==EXPECTED,mode+":counts",errors)
        check(receipt.get("digest")==EXPECTED_DIGEST,mode+":digest",errors)
        check(receipt.get("authority_grants")==0,mode+":authority",errors)
        expected_opt={"normal":0,"opt_flag":1,"env_opt":1}[mode]
        check(receipt.get("optimize")==expected_opt,mode+":optimization_mode",errors)
        check((root/(mode+".exit")).read_text(encoding="ascii").strip()=="0",mode+":exit",errors)
        err=(root/(mode+".stderr")).read_bytes()
        check(not err,mode+":stderr",errors)
    for mode in MODES:
        for control in ("stale_success","authority_success","retry_nonblocked","budget_monotonicity","row_count","outcome_count","oracle"):
            raw=(root/(mode+"-"+control+".control")).read_bytes()
            receipt=json.loads(raw)
            check(receipt.get("passed") is False,mode+":"+control+":must_reject",errors)
            check(receipt.get("pass_marker_seen") is False,mode+":"+control+":pass_marker",errors)
            check(isinstance(receipt.get("error"),str) and bool(receipt["error"]),mode+":"+control+":error",errors)
    report={"schema":"issue-4990-raw-audit-v1","errors":errors,"pass":not errors,
            "modes":list(MODES),"expected_digest":EXPECTED_DIGEST,"corruption_controls_per_mode":7}
    return report

if __name__=="__main__":
    root=Path(sys.argv[1]); report=audit(root); print(json.dumps(report,sort_keys=True))
    if not report["pass"]: raise SystemExit(1)
