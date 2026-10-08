"""Regression: schema-valid duplicate points pass endpoint preflight, not task parse."""
import json
import sys
from pathlib import Path
import hashlib
import os
from preflight_response_v1 import parse_schema_preflight

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
LIVE=ROOT/"research/live_control"
sys.path.insert(0,str(LIVE))
from plain_form_points_v1 import validate as validate_task_grounding
schema=LIVE/"plain_form_points_schema_v1.json"
raw={"format":"plain-form-points-v1",
    "field":{"point_space":"source_observation_pixels","point":{"x":400,"y":300}},
    "submit":{"point_space":"source_observation_pixels","point":{"x":400,"y":300}}}
OUT=HERE/"evidence/preflight-parser-test/run-02"
OUT.mkdir(parents=True,exist_ok=False)
events=OUT/"preflight-test-events.jsonl"
events.write_text("\n".join([
    json.dumps({"type":"thread.started","thread_id":"unit-preflight-1"}),
    json.dumps({"type":"item.completed","item":{"type":"error","message":"auxiliary retained"}}),
    json.dumps({"type":"item.completed","item":{"type":"agent_message","text":json.dumps(raw)}}),
    json.dumps({"type":"turn.completed","usage":{"input_tokens":10,"cached_input_tokens":0,"cache_write_input_tokens":0,"output_tokens":5,"reasoning_output_tokens":0}})])+"\n")
process=OUT/"preflight-test-process.json"
process.write_text(json.dumps({"exit_code":0,"authority_granted":False,
    "requested_model":"gpt-5.6-luna","requested_effort":"low"}))
result=parse_schema_preflight(events,process,schema)
assert result["schema_validation"]=="PASS_SCHEMA_ONLY" and result["call_id"]=="unit-preflight-1"
try: validate_task_grounding(raw)
except ValueError as exc:
    assert "must differ" in str(exc)
else: raise AssertionError("task grounding semantic validator unexpectedly accepted duplicates")
(OUT/"preflight-parser-test-result.json").write_text(json.dumps({
    "status":"PASS_SCHEMA_ONLY_SEPARATE_FROM_TASK_SEMANTICS",
    "schema_only_accepts_duplicate_points":True,"task_grounding_rejects_duplicate_points":True,
    "host_model_calls":0,"task_actions":0},indent=2)+"\n")
print("PASS_SCHEMA_ONLY_SEPARATE_FROM_TASK_SEMANTICS")
