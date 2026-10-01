"""Schema-only preflight parser; deliberately excludes task grounding semantics."""
from __future__ import annotations
import json
from pathlib import Path
from jsonschema import Draft202012Validator

USAGE_FIELDS={"input_tokens","cached_input_tokens","cache_write_input_tokens","output_tokens","reasoning_output_tokens"}

def parse_schema_preflight(events_path:Path,process_path:Path,schema_path:Path)->dict:
    events=[json.loads(line) for line in Path(events_path).read_text().splitlines() if line.strip()]
    process=json.loads(Path(process_path).read_text())
    schema=json.loads(Path(schema_path).read_text())
    Draft202012Validator.check_schema(schema)
    threads=[r for r in events if r.get("type")=="thread.started"]
    messages=[r.get("item",{}).get("text") for r in events if r.get("type")=="item.completed" and r.get("item",{}).get("type")=="agent_message"]
    turns=[r for r in events if r.get("type")=="turn.completed"]
    if len(threads)!=1 or len(messages)!=1 or len(turns)!=1:
        raise ValueError("one thread, assistant message, and completed turn required")
    raw=json.loads(messages[0])
    if type(raw) is not dict: raise ValueError("schema preflight output must be one JSON object")
    errors=list(Draft202012Validator(schema).iter_errors(raw))
    if errors: raise ValueError("schema preflight output fails schema: "+errors[0].message)
    usage=turns[0].get("usage")
    if type(usage) is not dict or not USAGE_FIELDS<=set(usage):
        raise ValueError("complete endpoint usage required")
    if process.get("exit_code")!=0 or process.get("authority_granted") is not False:
        raise ValueError("successful non-authoritative runner receipt required")
    return {"raw":raw,"call_id":threads[0].get("thread_id"),"usage":usage,
        "requested_model":process.get("requested_model"),
        "requested_effort":process.get("requested_effort"),"cost":None,
        "schema_validation":"PASS_SCHEMA_ONLY"}
