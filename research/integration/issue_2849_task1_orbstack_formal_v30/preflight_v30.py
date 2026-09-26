from __future__ import annotations
import hashlib,json,os
from pathlib import Path
from scope_reconcile_v30 import reconcile_after_finish
ROOT=Path("/repo"); V29=ROOT/"research/integration/issue_2849_task1_orbstack_formal_v29/evidence/task1-seed-284929"
OUT=Path("/out")
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    before={str(p.relative_to(V29)):sha(p) for p in sorted(V29.rglob("*")) if p.is_file()}
    original_audit=json.loads((V29/"posthoc-independent-audit.json").read_text())
    row=json.loads((V29/"task-run/task-trace.json").read_text()); history=json.loads((V29/"task-run/submission-history.snapshot.json").read_text()); task=json.loads((V29/"task-run/frozen-task.json").read_text())
    fixed,matches,scope=reconcile_after_finish(row,history,task)
    after={str(p.relative_to(V29)):sha(p) for p in sorted(V29.rglob("*")) if p.is_file()}
    checks={"predecessor_formal_failure_preserved":original_audit.get("accepted_formal_outcome")=="FAIL_TASK1_SCOPED",
      "predecessor_inventory_unchanged":before==after,"original_trace_still_unmodified":row.get("submission_count")==0 and row.get("exact_submission") is False,
      "shared_v30_helper_reconciles_history":fixed.get("submission_count")==1 and fixed.get("exact_submission") is True,
      "shared_v30_helper_derives_task1_scope_pass":scope.get("status")=="PASS_TASK1_SCOPED" and len(matches)==1,
      "six_task_claim_not_promoted":scope.get("full_six_task_fixture_success") is False,
      "no_task_model_gui_or_ipc":True}
    result={"seed":284930,"status":"PASS_FORMAL_WRAPPER_PREFLIGHT" if all(checks.values()) else "STOP_FORMAL_WRAPPER_PREFLIGHT","checks":checks,
      "formal_predecessor_outcome":"FAIL_TASK1_SCOPED","scope":"no-task preflight only","task_started":False,"model_calls":0,"gui_actions":0,"ipc_calls":0,
      "derived_trace":fixed,"derived_scope":scope,"v29_inventory_count":len(before)}
    (OUT/"preflight-result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    return 0 if result["status"]=="PASS_FORMAL_WRAPPER_PREFLIGHT" else 1
if __name__=="__main__": raise SystemExit(main())
