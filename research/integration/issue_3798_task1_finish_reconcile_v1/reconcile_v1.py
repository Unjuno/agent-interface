from __future__ import annotations
import json
from pathlib import Path

def reconcile(trace: dict, history: list[dict], task: dict) -> tuple[dict, dict]:
    row=dict(trace)
    matching=[record for record in history if record.get("task_id")==row.get("task_id")]
    row["submission_count"]=len(matching)
    row["exact_submission"]=(len(matching)==1 and matching[0].get("exact") is True)
    expected=task.get("token")
    scope_ok=(row.get("typed_outcome")=="completed"
        and row.get("model_visible_images")==1
        and len(row.get("model_calls",[]))==1
        and row.get("submission_count")==1
        and row.get("exact_submission") is True
        and row.get("releases_verified") is True
        and len(matching)==1
        and matching[0].get("exact") is True
        and matching[0].get("submitted_values")==[expected]
        and matching[0].get("expected_token")==expected
        and len(history)==1)
    scope={"status":"PASS_TASK1_SCOPED" if scope_ok else "FAIL_TASK1_SCOPED",
        "exact_submission_count":len(matching),"total_fixture_submission_count":len(history),
        "runtime_releases_verified":row.get("releases_verified"),"model_call_count":len(row.get("model_calls",[])),
        "authority_granted":False}
    return row,scope

def main():
    import os
    source=Path(os.environ["ISSUE3798_INPUT"])
    out=Path(os.environ["ISSUE3798_OUTPUT"])
    v29=json.loads((source/"task-run/task-trace.json").read_text())
    history=json.loads((source/"task-run/submission-history.snapshot.json").read_text())
    task=json.loads((source/"task-run/frozen-task.json").read_text())
    row,scope=reconcile(v29,history,task)
    (out/"reconciled-trace.json").write_text(json.dumps(row,indent=2,sort_keys=True)+"\n")
    (out/"reconciled-scope.json").write_text(json.dumps(scope,indent=2,sort_keys=True)+"\n")
    return row,scope

if __name__=="__main__": main()
