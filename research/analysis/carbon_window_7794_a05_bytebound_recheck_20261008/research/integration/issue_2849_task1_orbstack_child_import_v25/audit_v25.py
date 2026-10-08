from __future__ import annotations
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent; RUN=HERE/"evidence/seed-284925"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    frozen=json.loads((RUN/"frozen-inputs.json").read_text()); result=json.loads((RUN/"probe-result.json").read_text())
    source=HERE/"probe_v25.py"
    checks={"probe_hash_matches_freeze":sha(source)==frozen["probe_sha256"],"all_six_child_imports_pass":result["checks"]["child_imports_all_expected_modules"],
      "outer_returned_zero":result["outer_returncode"]==0,"task_token_gui_broker_model_absent":result["task_started"] is False and result["task_token_acquired"] is False and result["gui_started"] is False and result["broker_started"] is False and result["model_calls"]==0,
      "registered_status_pass":result["status"]=="PASS_CHILD_IMPORTS"}
    audit={"seed":284925,"status":"PASS_CHILD_IMPORTS" if all(checks.values()) else "STOP_CHILD_IMPORTS","checks":checks,
      "scope":"child-process import path only; no task/runtime/model","authority_granted":False,
      "probe_sha256":sha(source),"frozen_inputs_sha256":sha(RUN/"frozen-inputs.json"),"probe_result_sha256":sha(RUN/"probe-result.json")}
    (RUN/"independent-audit.json").write_text(json.dumps(audit,indent=2,sort_keys=True)+"\n")
    files=sorted(p for p in RUN.rglob("*") if p.is_file() and p.name!="SHA256SUMS")
    (RUN/"SHA256SUMS").write_text("".join(f"{sha(p)}  {p.relative_to(RUN)}\n" for p in files))
    return 0 if all(checks.values()) else 1
if __name__=="__main__": raise SystemExit(main())
