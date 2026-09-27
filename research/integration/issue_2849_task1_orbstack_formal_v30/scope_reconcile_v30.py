from __future__ import annotations

def reconcile_after_finish(row: dict, records: list[dict], task: dict) -> tuple[dict, list[dict], dict]:
    reconciled=dict(row)
    matching=[record for record in records if record.get("task_id")==reconciled.get("task_id")]
    reconciled["submission_count"]=len(matching)
    reconciled["exact_submission"]=(len(matching)==1 and matching[0].get("exact") is True)
    if len(matching)==1:
        reconciled["source_to_completion_ns"]=matching[0]["received_ns"]-task["source_capture_ns"] if "source_capture_ns" in task else reconciled.get("source_to_completion_ns")
    token=task.get("token")
    passed=(reconciled.get("typed_outcome")=="completed" and reconciled.get("model_visible_images")==1
      and len(reconciled.get("model_calls",[]))==1 and reconciled.get("submission_count")==1
      and reconciled.get("exact_submission") is True and reconciled.get("releases_verified") is True
      and len(matching)==1 and matching[0].get("exact") is True
      and matching[0].get("submitted_values")==[token] and matching[0].get("expected_token")==token
      and len(records)==1)
    scope={"status":"PASS_TASK1_SCOPED" if passed else "FAIL_TASK1_SCOPED",
      "task_id":reconciled.get("task_id"),"exact_submission_count":len(matching),
      "total_fixture_submission_count":len(records),"full_six_task_fixture_success":False,
      "model_call_count":len(reconciled.get("model_calls",[])),"model_visible_images":reconciled.get("model_visible_images"),
      "runtime_releases_verified":reconciled.get("releases_verified"),"authority_granted":False}
    return reconciled,matching,scope
