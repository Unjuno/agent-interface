import json,pathlib
r=json.loads((pathlib.Path(__file__).parent/"RESULT.json").read_text())
checks={
 "rows_32":r["rows"]==32,
 "positive_4":r["revalidated"]==4,
 "stale_28":r["stale"]==28,
 "classification_exact":r["classification_mismatches"]==0,
 "cross_session_zero":r["cross_session_accepts"]==0,
 "cross_resource_zero":r["cross_resource_accepts"]==0,
 "stale_current_zero":r["stale_current_accepts"]==0,
 "controls_reject":r["control_accepts"]==0 and len(r["controls"])==5,
 "commit_never_persisted":r["persistent_commit_receipts"]==0,
 "budget":r["formal_invocations"]==1 and r["reruns"]==0 and r["replacements"]==0 and r["tuning"]==0,
 "decision_pass":r["decision"]=="PASS_REUSABLE_RECEIPT_SESSION_RESOURCE_BINDING_SCOPED"
}
out={"checks":checks,"pass":all(checks.values())}
print(json.dumps(out,indent=2,sort_keys=True))
raise SystemExit(0 if out["pass"] else 1)
