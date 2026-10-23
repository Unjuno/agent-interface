"""R06 auditor: scores direct raw public result and independent fixture oracle."""
import json
from pathlib import Path
root=Path(__file__).resolve().parent
conditions=json.loads((root/"conditions.json").read_text(encoding="utf-8"))
raw=json.loads((root/"raw.json").read_text(encoding="utf-8"))
expected=conditions["task"]["text"]
result=raw.get("retained_report",{}).get("result",{})
execution=result.get("execution",{})
releases=execution.get("releases",[])
release=releases[-1] if releases else {}
events=raw.get("fixture_events",[])
chars=[e for e in events if e.get("kind")=="char"]
saves=[e for e in events if e.get("kind")=="save"]
checks={
 "attempt_and_source_match":raw.get("attempt_id")==conditions["attempt_id"] and raw.get("source_commit")==conditions["source_commit"],
 "actual_public_stdio_route":raw.get("caller_kind")=="mcp_stdio" and {"interface_observe","interface_dispatch"}.issubset(raw.get("listed_tools",[])),
 "observation_returned":raw.get("observation",{}).get("is_error") is False and bool(raw.get("observation",{}).get("content")),
 "public_preflight_valid":raw.get("program_validation",{}).get("static_valid") is True,
 "runtime_completed":result.get("status")=="completed" and result.get("recovery_required") is False,
 "owned_fixture_retired":raw.get("fixture_close_posted") is True and raw.get("fixture_exit_code")==0,
 "exactly_one_dispatch":raw.get("dispatch_attempts")==1,
 "independent_task_effect":raw.get("effect_file")=={"saved":True,"text":expected,"clicked":True},
 "exact_event_count_and_text":type(raw.get("oracle",{}).get("char_event_count")) is int and raw["oracle"]["char_event_count"]==len(expected) and "".join(chr(e["code"]) for e in chars)==expected,
 "one_save_event":len(saves)==1,
 "release_verified":len(releases)==1 and release.get("verified") is True and release.get("keys_down")==[] and release.get("buttons_down")==[] and release.get("keys_unknown")==[] and release.get("buttons_unknown")==[],
 "release_matches_probe_oracle":raw.get("oracle",{}).get("release_receipt")==release and raw.get("oracle",{}).get("release_pass") is True,
 "target_generation_recorded":isinstance(raw.get("target_identity_before"),dict) and raw.get("target_identity_before")==raw.get("target_identity_after"),
 "no_presentation_claim":raw.get("oracle",{}).get("nonclaims")==conditions["nonclaims"],
}
audit={"schema":"win32-public-mcp-live-effect-audit-v1","attempt_id":conditions["attempt_id"],"checks":checks,"passed":sum(checks.values()),"total":len(checks),"status":"PASS" if all(checks.values()) else "FAIL","experiment_outcome":raw.get("status")}
(root/"audit.json").write_text(json.dumps(audit,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(audit,indent=2,sort_keys=True))
raise SystemExit(0 if all(checks.values()) else 1)
