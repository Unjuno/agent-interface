from __future__ import annotations
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[2]; RUN=HERE/"evidence/seed-284928"
V26=ROOT/"research/integration/issue_2849_task1_orbstack_formal_v26/evidence/task1-seed-284926"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())
def main():
    frozen=read(RUN/"frozen-inputs.json"); result=read(RUN/"replay-result.json"); outer=read(RUN/"outer-result.json")
    original=V26/"ipc/d8b2c076c08f48229b18484e2ca4a419.response.jsonl"; events=RUN/"backend-call/runner/events.jsonl"
    process=read(RUN/"backend-call/runner/process.json"); validation=read(RUN/"backend-call/schema-validation.json")
    ground=result.get("grounding") or {}; field=ground.get("field_point"); submit=ground.get("submit_point")
    points=isinstance(field,list) and isinstance(submit,list) and len(field)==len(submit)==2 and field!=submit and all(type(n) is int and 0<=n<1280 for n in field+submit)
    checks={"all_frozen_source_hashes_match":all(sha(ROOT/path)==digest for path,digest in frozen["source_hashes"].items()),
      "response_and_image_inputs_match_freeze":sha(original)==frozen["response_sha256"] and sha(V26/"host-model-mirror/image.png")==frozen["screenshot_sha256"],
      "raw_response_preserved_byte_for_byte":events.is_file() and sha(events)==sha(original),
      "corrected_runner_counts_message_turn_and_retains_error":process.get("assistant_message_count")==1 and process.get("completed_turn_count")==1 and process.get("ignored_non_assistant_item_completed_count")==1 and process.get("event_count")==5,
      "main_schema_validator_pass":validation.get("status")=="PASS" and validation.get("schema_valid") is True,
      "main_plain_parser_returns_bounded_distinct_points":points,
      "one_outer_one_nested_returned_zero":outer.get("outer_invocations")==1 and outer.get("outer_returncode")==0 and result.get("nested_container_invocations")==1,
      "no_host_model_task_or_authority":result.get("task_started") is False and result.get("task_token_acquired") is False and result.get("host_broker_started") is False and result.get("host_codex_invoked") is False and result.get("model_calls")==0 and result.get("authority_granted") is False,
      "registered_replay_status_pass":result.get("status")=="PASS_RESPONSE_REPLAY"}
    audit={"issue":2849,"seed":284928,"status":"PASS_RESPONSE_REPLAY" if all(checks.values()) else "STOP_RESPONSE_REPLAY","checks":checks,
      "scope":"saved response through additive nested runner and unchanged selected backend/schema/plain parser; no task/model",
      "input_response_sha256":sha(original),"replayed_events_sha256":sha(events) if events.is_file() else None,"authority_granted":False}
    (RUN/"independent-audit.json").write_text(json.dumps(audit,indent=2,sort_keys=True)+"\n")
    files=sorted(p for p in RUN.rglob("*") if p.is_file() and p.name!="SHA256SUMS")
    (RUN/"SHA256SUMS").write_text("".join(f"{sha(p)}  {p.relative_to(RUN)}\n" for p in files))
    return 0 if all(checks.values()) else 1
if __name__=="__main__": raise SystemExit(main())
