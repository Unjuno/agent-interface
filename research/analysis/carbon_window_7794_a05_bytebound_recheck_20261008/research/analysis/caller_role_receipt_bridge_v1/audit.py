import json,pathlib
root=pathlib.Path(__file__).parent
r=json.loads((root/"RESULT.json").read_text())
rows={x["name"]:x for x in r["rows"]}
neg=("stale_dependency","false_gate","missing_gate","prior_epoch_replay",
     "wrong_intent","persist_commit_attempt","unknown_role")
checks={
 "caller_blob_exact":r["caller_blob"]=="7faf042304728ce91a3e4f89d465b251ea0bf70d",
 "scenario_count":r["scenario_count"]==10,
 "positive_success":rows["positive"]["outcome"]=="TASK_SUCCEEDED" and rows["positive"]["execute_count"]==1,
 "negatives_no_execute":all(rows[n]["execute_count"]==0 and rows[n]["input_authority"]=="none" for n in neg),
 "stale_stops_before_final":rows["stale_dependency"]["final_stage"]["status"]=="skipped",
 "gate_negatives_final_or_before":all(rows[n]["execute_stage"]["status"]=="skipped" for n in
   ("false_gate","missing_gate","prior_epoch_replay","wrong_intent","persist_commit_attempt","unknown_role")),
 "commit_never_persisted":r["persistent_commit_receipts"]==0,
 "replay_accepts_zero":r["cross_intent_epoch_replay_accepts"]==0,
 "persist_attempt_rejected":rows["persist_commit_attempt"]["persist_gate_result"] is False,
 "unknown_role_rejected":"bad_gate_role_or_storage" in rows["unknown_role"]["bridge_rejections"],
 "pair_first_success":r["paired"]["first_outcome"]=="TASK_SUCCEEDED" and r["paired"]["first_execute"]==1,
 "pair_second_stops":r["paired"]["second_execute"]==0,
 "pair_dependency_reused":r["paired"]["persistent_roles"]==["PREPARED_REUSABLE_VERSIONED"],
 "budget":r["formal_invocations"]==1 and r["reruns"]==0 and r["replacements"]==0 and r["tuning"]==0,
 "decision_pass":r["decision"]=="PASS_CALLER_ROLE_RECEIPT_BRIDGE_SCOPED",
}
out={"checks":checks,"pass":all(checks.values())}
print(json.dumps(out,indent=2,sort_keys=True))
raise SystemExit(0 if out["pass"] else 1)
