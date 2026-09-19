"""Public golden-v3 result boundary over the existing CLI dispatch API."""
from __future__ import annotations
from typing import Any, Mapping
from .api import dispatch

STATUSES={"invalid_request","backend_unavailable","runtime_failed","returned"}
LIFECYCLE={"doctor","model_attempt","observation","dispatch","refusal","effect","repair","release","cleanup"}

def adapt_dispatch_result(result: dict[str,Any], *, usage: Mapping[str,Any]|None=None, lifecycle: list[str]|None=None) -> dict[str,Any]:
    status=result.get("status")
    states=list(lifecycle) if lifecycle is not None else ["dispatch"]
    if status not in STATUSES:
        return _reject("UNKNOWN_STATUS", result, usage)
    if any(state not in LIFECYCLE for state in states):
        return _reject("UNKNOWN_LIFECYCLE", result, usage)
    cleanup=result.get("cleanup_error")
    nested=result.get("result") if isinstance(result.get("result"),dict) else {}
    if cleanup is not None: mapped="cleanup_failed"
    elif status in {"invalid_request","backend_unavailable"}: mapped="refused"
    elif status=="runtime_failed": mapped="partial"
    else: mapped="success" if nested.get("program_completed") is True and nested.get("task_success") is True else "partial"
    row={"schema":"golden-v3-result-v1","program_completed":mapped=="success","task_success":mapped=="success",
         "authority_granted":False,"status":mapped,"partial_effects":nested.get("partial_effects",[]),
         "cleanup_error":cleanup,"lifecycle":states,"usage":dict(usage or result.get("usage") or {})}
    if cleanup is not None: row["task_success"]=False
    if "error" in result: row["diagnostic"]=result["error"]
    return row

def _reject(reason:str,result:dict[str,Any],usage:Mapping[str,Any]|None)->dict[str,Any]:
    return {"schema":"golden-v3-result-v1","program_completed":False,"task_success":False,
            "authority_granted":False,"status":"refused","partial_effects":[],"cleanup_error":None,
            "lifecycle":[],"usage":dict(usage or result.get("usage") or {}),
            "adapter_error":reason,"diagnostic":result.get("error")}

def dispatch_golden_v3(program:dict[str,Any],targets:Mapping[str,int],*,current_observation_seq:int,
                       current_binding_revision:int,display_name:str|None=None,
                       usage:Mapping[str,Any]|None=None)->dict[str,Any]:
    raw=dispatch(program,targets,current_observation_seq=current_observation_seq,
                 current_binding_revision=current_binding_revision,display_name=display_name)
    return adapt_dispatch_result(raw,usage=usage)
