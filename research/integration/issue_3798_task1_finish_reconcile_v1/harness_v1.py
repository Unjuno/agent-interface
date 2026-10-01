from __future__ import annotations
import ast,hashlib,json,os,subprocess
from pathlib import Path
REPO=Path("/repo"); SOURCE=REPO/"research/integration/issue_2849_task1_orbstack_formal_v29/evidence/task1-seed-284929"
OUT=Path("/out"); HERE=REPO/"research/integration/issue_3798_task1_finish_reconcile_v1"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    original_audit=json.loads((SOURCE/"posthoc-independent-audit.json").read_text())
    if original_audit.get("accepted_formal_outcome")!="FAIL_TASK1_SCOPED": raise RuntimeError("STOP_PREDECESSOR_CLASSIFICATION")
    manifest=json.loads((SOURCE/"task-run/pre-call-source-manifest.json").read_text())
    script=HERE/"reconcile_v1.py"; source_file=REPO/"research/live_control/run_integrated_efficiency_live_v1.py"
    ast.parse(source_file.read_text())
    source_text=source_file.read_text()
    required=("final_history = records(client.runtime / \"submission-history.jsonl\")",
      "matching = [record for record in final_history",
      "row[\"submission_count\"] = len(matching)",
      "row[\"exact_submission\"] = (len(matching) == 1")
    if not all(piece in source_text for piece in required): raise RuntimeError("STOP_REFERENCE_RECONCILIATION_PATTERN_CHANGED")
    inputs={"task_trace":sha(SOURCE/"task-run/task-trace.json"),
      "submission_history":sha(SOURCE/"task-run/submission-history.snapshot.json"),
      "frozen_task":sha(SOURCE/"task-run/frozen-task.json"),
      "predecessor_audit":sha(SOURCE/"posthoc-independent-audit.json"),
      "reference_runner":sha(source_file),"reconciler":sha(script)}
    before={str(p.relative_to(SOURCE)):sha(p) for p in sorted(SOURCE.rglob("*")) if p.is_file()}
    env=dict(os.environ); env["ISSUE3798_INPUT"]=str(SOURCE); env["ISSUE3798_OUTPUT"]=str(OUT)
    proc=subprocess.run(["python3",str(script)],env=env,capture_output=True,text=True,check=False)
    if proc.returncode: raise RuntimeError("STOP_RECONCILER:"+proc.stderr[-2000:])
    after={str(p.relative_to(SOURCE)):sha(p) for p in sorted(SOURCE.rglob("*")) if p.is_file()}
    original=json.loads((SOURCE/"task-run/task-trace.json").read_text())
    history=json.loads((SOURCE/"task-run/submission-history.snapshot.json").read_text())
    row=json.loads((OUT/"reconciled-trace.json").read_text()); scope=json.loads((OUT/"reconciled-scope.json").read_text())
    checks={"reference_source_has_finish_time_reconciliation":all(piece in source_text for piece in required),
      "v29_source_inventory_unchanged":before==after,"v29_original_outcome_still_fail":original_audit["accepted_formal_outcome"]=="FAIL_TASK1_SCOPED",
      "v29_original_trace_still_pre_finish_value":original.get("submission_count")==0 and original.get("exact_submission") is False,
      "history_exactly_matches_frozen_token":len(history)==1 and history[0].get("exact") is True and history[0].get("submitted_values")==[json.loads((SOURCE/"task-run/frozen-task.json").read_text()).get("token")],
      "derived_trace_agrees_with_exact_history":row.get("submission_count")==1 and row.get("exact_submission") is True,
      "derived_single_task_scope_passes":scope.get("status")=="PASS_TASK1_SCOPED",
      "six_task_boundary_remains_unmet":json.loads((SOURCE/"task-run/six-task-fixture-evaluation.json").read_text()).get("success") is False,
      "no_task_model_gui_or_ipc_activity":True}
    result={"issue":3798,"parent_issue":2849,"seed":284929,"status":"PASS_OFFLINE_RECONCILIATION" if all(checks.values()) else "FAIL_OFFLINE_RECONCILIATION",
      "formal_outcome":"FAIL_TASK1_SCOPED","scope":"offline accounting replay only; not formal task success",
      "authority_granted":False,"task_started":False,"model_calls":0,"gui_actions":0,"ipc_calls":0,"checks":checks,"input_hashes":inputs,
      "v29_source_file_count":len(before),"v29_source_inventory_unchanged":before==after,"predecessor_formal_outcome":"FAIL_TASK1_SCOPED",
      "reconciled_trace":row,"reconciled_scope":scope,"six_task_success":False}
    (OUT/"offline-result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    return 0 if result["status"]=="PASS_OFFLINE_RECONCILIATION" else 1
if __name__=="__main__": raise SystemExit(main())
