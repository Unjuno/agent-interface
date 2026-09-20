from __future__ import annotations
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[2]; RUN=HERE/"evidence/seed-284927"
V26=HERE.parent/"issue_2849_task1_orbstack_formal_v26/evidence/task1-seed-284926"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())
def main():
    frozen=read(RUN/"frozen-inputs.json"); result=read(RUN/"replay-result.json"); outer=read(RUN/"outer-result.json")
    original=V26/"ipc/d8b2c076c08f48229b18484e2ca4a419.response.jsonl"
    source=HERE/"runner_v27.py"; out=RUN/"backend-call"; events=out/"runner/events.jsonl"
    runner=read(out/"runner/process.json") if (out/"runner/process.json").is_file() else {}
    validation=read(out/"schema-validation.json") if (out/"schema-validation.json").is_file() else {}
    checks={"runner_source_hash_matches_freeze":sha(source)==frozen["local_sources"][str(source.relative_to(ROOT))],
      "predecessor_response_hash_matches_freeze":sha(original)==frozen["predecessor_response_sha256"],
      "raw_response_byte_preserved":events.is_file() and sha(events)==sha(original),
      "single_agent_message_and_turn_with_error_retained":runner.get("assistant_message_count")==1 and runner.get("completed_turn_count")==1 and runner.get("ignored_non_assistant_item_completed_count")==1 and runner.get("event_count")==5,
      "main_schema_validation_pass":validation.get("status")=="PASS" and validation.get("schema_valid") is True,
      "main_plain_parser_returned_distinct_bounded_points":False,
      "outer_one_nested_call_returned_zero":outer.get("outer_invocations")==1 and outer.get("outer_returncode")==0 and result.get("nested_container_invocations")==1,
      "no_task_or_host_model_activity":result.get("task_started") is False and result.get("task_token_acquired") is False and result.get("host_broker_started") is False and result.get("host_codex_invoked") is False and result.get("model_calls")==0,
      "result_status_pass":result.get("status")=="PASS_RESPONSE_REPLAY"}
    grounding=result.get("grounding") or {}; field=grounding.get("field_point"); submit=grounding.get("submit_point")
    checks["main_plain_parser_returned_distinct_bounded_points"]=(isinstance(field,list) and isinstance(submit,list) and len(field)==len(submit)==2 and field!=submit and all(type(x) is int and 0<=x<1280 for x in field) and all(type(x) is int and 0<=x<1280 for x in submit))
    checks["v27_source_manifest_all_local_hashes_match"]=all(sha(ROOT/path)==digest for path,digest in frozen["local_sources"].items())
    audit={"issue":2849,"seed":284927,"status":"PASS_RESPONSE_REPLAY" if all(checks.values()) else "STOP_RESPONSE_REPLAY","checks":checks,
      "scope":"saved-response compatibility through nested runner, main selected backend schema gate and plain parser; no task/model",
      "predecessor_response_sha256":sha(original),"replayed_events_sha256":sha(events) if events.is_file() else None,
      "authority_granted":False}
    (RUN/"independent-audit.json").write_text(json.dumps(audit,indent=2,sort_keys=True)+"\n")
    files=sorted(p for p in RUN.rglob("*") if p.is_file() and p.name!="SHA256SUMS")
    (RUN/"SHA256SUMS").write_text("".join(f"{sha(p)}  {p.relative_to(RUN)}\n" for p in files))
    return 0 if all(checks.values()) else 1
if __name__=="__main__": raise SystemExit(main())
