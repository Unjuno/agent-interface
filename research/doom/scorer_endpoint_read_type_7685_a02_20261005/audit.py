import hashlib
import json
import subprocess
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
PKG = Path(__file__).resolve().parent


def main():
    freeze=json.loads((PKG/"FREEZE.json").read_text(encoding="utf-8")); result=json.loads((PKG/"RESULT.json").read_text(encoding="utf-8"))
    raw=subprocess.check_output(["git","show",f"{freeze['subject_pr_head']}:{freeze['source_path']}"],cwd=ROOT)
    cases={r.get("case"):r for r in result.get("cases",[])}
    checks={
        "source_pin_matches":hashlib.sha256(raw).hexdigest()==freeze["source_sha256"]==result.get("source_sha256"),
        "subject_head_matches":result.get("subject_pr_head")==freeze["subject_pr_head"],
        "case_inventory_exact":set(cases)=={"integer_control","float_alias","bool_alias"},
        "integer_control_qualifies":cases.get("integer_control",{}).get("receipt_status")=="REFRESH_RETURNED_RUNTIME_QUALIFICATION_PENDING" and cases.get("integer_control",{}).get("values_present") is True,
        "float_alias_qualifies":cases.get("float_alias",{}).get("readback")=={"value":11.0,"type":"float"} and cases.get("float_alias",{}).get("after")=={"value":11,"type":"int"} and cases.get("float_alias",{}).get("receipt_status")=="REFRESH_RETURNED_RUNTIME_QUALIFICATION_PENDING",
        "bool_alias_qualifies":cases.get("bool_alias",{}).get("readback")=={"value":True,"type":"bool"} and cases.get("bool_alias",{}).get("after")=={"value":1,"type":"int"} and cases.get("bool_alias",{}).get("receipt_status")=="REFRESH_RETURNED_RUNTIME_QUALIFICATION_PENDING",
        "decision_matches_cases":result.get("decision")=="FAIL_OPEN_ENDPOINT_TYPE",
    }
    report={"schema":"scorer-endpoint-read-type-7685-a02-independent-audit-v1","pass":all(checks.values()),"checks":checks,"errors":[k for k,v in checks.items() if not v],"scope":"saved-output and source-pin audit; candidate is not re-executed"}
    (PKG/"AUDIT.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps(report,indent=2)); raise SystemExit(0 if report["pass"] else 1)


if __name__=="__main__":main()
