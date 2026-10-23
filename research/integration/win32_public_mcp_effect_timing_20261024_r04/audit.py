"""Frozen auditor for one public Win32 effect-timing sample."""
import json
import hashlib
from pathlib import Path
root=Path(__file__).resolve().parent
conditions=json.loads((root/"conditions.json").read_text(encoding="utf-8"))
raw=json.loads((root/"raw.json").read_text(encoding="utf-8"))
expected=conditions["task"]["text"]
file_hashes={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in conditions.get("frozen_files",{})}
result=raw.get("retained_report",{}).get("result",{})
execution=result.get("execution",{})
releases=execution.get("releases",[])
release=releases[-1] if releases else {}
events=raw.get("fixture_events",[])
observations=execution.get("observations",[])
final_capture=observations[-1] if observations else {}
final_artifact=final_capture.get("artifact",{})
final_artifact_path=Path(final_artifact.get("path",".")).resolve()
artifact_inside_packet=root.resolve() in final_artifact_path.parents
artifact_hash_matches=(artifact_inside_packet and final_artifact_path.is_file()
    and hashlib.sha256(final_artifact_path.read_bytes()).hexdigest()==final_artifact.get("sha256"))
chars=[e for e in events if e.get("kind")=="char"]
saves=[e for e in events if e.get("kind")=="save"]
checks={
 "attempt_and_source_match":raw.get("attempt_id")==conditions["attempt_id"] and raw.get("source_commit")==conditions["source_commit"],
 "frozen_protocol_hashes_match":file_hashes==conditions.get("frozen_files"),
 "actual_public_stdio_route":raw.get("caller_kind")=="mcp_stdio" and {"interface_observe","interface_dispatch"}.issubset(raw.get("listed_tools",[])),
 "observation_returned":raw.get("observation",{}).get("is_error") is False and bool(raw.get("observation",{}).get("content")),
 "public_preflight_valid":raw.get("program_validation",{}).get("static_valid") is True,
 "runtime_completed":result.get("status")=="completed" and result.get("recovery_required") is False,
 "owned_fixture_retired":raw.get("fixture_close_posted") is True and raw.get("fixture_exit_code")==0,
 "exactly_one_dispatch":raw.get("dispatch_attempts")==1,
 "independent_task_effect":raw.get("effect_file")=={"saved":True,"text":expected,"clicked":True},
 "exact_event_count_and_text":type(raw.get("oracle",{}).get("char_event_count")) is int and raw["oracle"]["char_event_count"]==len(expected) and "".join(chr(e["code"]) for e in chars)==expected,
 "exactly_one_click_event":sum(e.get("kind")=="click" for e in events)==1,
 "one_save_event":len(saves)==1,
 "release_verified":len(releases)==1 and release.get("verified") is True and release.get("keys_down")==[] and release.get("buttons_down")==[] and release.get("keys_unknown")==[] and release.get("buttons_unknown")==[],
 "release_matches_probe_oracle":raw.get("oracle",{}).get("release_receipt")==release and raw.get("oracle",{}).get("release_pass") is True,
 "target_generation_recorded":isinstance(raw.get("target_identity_before"),dict) and raw.get("target_identity_before")==raw.get("target_identity_after"),
 "complete_timed_event_set_inside_dispatch":sum(e.get("kind") in {"click","char","save"} for e in events)==len(expected)+2 and all(isinstance(e.get("monotonic_ns"),int) and raw.get("dispatch",{}).get("started_monotonic_ns",0) <= e["monotonic_ns"] <= raw.get("dispatch",{}).get("returned_monotonic_ns",-1) for e in events if e.get("kind") in {"click","char","save"}),
 "observed_generation_forwarded":isinstance(raw.get("observed_target_generation"),str) and raw.get("program",{}).get("source",{}).get("target_generations",{}).get("fixture")==raw.get("observed_target_generation"),
 "observation_generation_matched_independent_read":raw.get("observation_target_generation_consistency")=="matched" and raw.get("observed_target_generation")==raw.get("target_identity_before",{}).get("generation"),
 "high_resolution_clock_documented":raw.get("timing_clock",{}).get("monotonic") is True and raw.get("timing_clock",{}).get("implementation")=="QueryPerformanceCounter()" and isinstance(raw.get("timing_clock",{}).get("resolution_seconds"),(int,float)) and raw["timing_clock"]["resolution_seconds"]<=0.000001,
 "post_action_full_width_capture":final_capture.get("target")=="fixture" and final_capture.get("width")==420 and final_capture.get("height")==140 and final_artifact.get("width")==420,
 "post_action_image_retained_and_hash_matches":artifact_hash_matches and final_artifact.get("source_raw_sha256")==final_capture.get("sha256"),
 "commit_before_public_return":isinstance(saves[0].get("commit_completed_monotonic_ns"),int) and saves[0]["commit_completed_monotonic_ns"] <= raw.get("dispatch",{}).get("returned_monotonic_ns",-1) if len(saves)==1 else False,
 "independent_readback_after_commit":isinstance(raw.get("effect_read_started_monotonic_ns"),int) and raw["effect_read_started_monotonic_ns"] >= saves[0].get("commit_completed_monotonic_ns",2**63) if len(saves)==1 else False,
 "all_timing_durations_nonnegative":all(isinstance(v,(int,float)) and v>=0 for k,v in raw.get("timing",{}).items() if k.endswith("_ms")),
 "release_receipt_timing_limit_disclosed":raw.get("timing",{}).get("release_timing_interpretation")=="release receipt and final state are observed no later than the public dispatch response; exact release call timestamp is not exposed",
 "positive_generation_admission":raw.get("retained_report",{}).get("result",{}).get("status")=="completed" and raw.get("program",{}).get("source",{}).get("target_generations",{}).get("fixture")==raw.get("observed_target_generation"),
 "nonclaims_preserved":raw.get("oracle",{}).get("nonclaims")==conditions["nonclaims"],
}
audit={"schema":"win32-public-mcp-effect-timing-audit-v1","attempt_id":conditions["attempt_id"],"checks":checks,"passed":sum(checks.values()),"total":len(checks),"status":"PASS" if all(checks.values()) else "FAIL","experiment_outcome":raw.get("status")}
(root/"audit.json").write_text(json.dumps(audit,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(audit,indent=2,sort_keys=True))
raise SystemExit(0 if all(checks.values()) else 1)
