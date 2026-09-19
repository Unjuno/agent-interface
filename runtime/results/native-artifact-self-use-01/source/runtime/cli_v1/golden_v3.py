"""Public golden-v3 result boundary over the existing CLI dispatch API."""
from __future__ import annotations
from copy import deepcopy
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
    native_status=nested.get("status")
    # Native sessions return status, not the legacy golden success flags.
    # Completion does not supply an independent application score.
    completed=(native_status=="completed" if native_status is not None
               else nested.get("program_completed") is True)
    task_success=nested.get("task_success")
    if type(task_success) is not bool:
        task_success=None
    if cleanup is not None: mapped="cleanup_failed"
    elif status in {"invalid_request","backend_unavailable"}: mapped="refused"
    elif status=="runtime_failed": mapped="partial"
    elif native_status=="refused": mapped="refused"
    else: mapped="success" if completed and task_success is True else "partial"
    row={"schema":"golden-v3-result-v2","program_completed":completed,"task_success":task_success,
         "authority_granted":False,"status":mapped,"partial_effects":nested.get("partial_effects",[]),
         "cleanup_error":cleanup,"lifecycle":states,"usage":dict(usage if usage is not None else result.get("usage") or {}),
         "native_status":native_status,"raw_dispatch":deepcopy(result)}
    # Overall task success remains false after cleanup failure. The supplied
    # application score and completed execution are still in raw_dispatch.
    if cleanup is not None: row["task_success"]=False
    if "error" in result: row["diagnostic"]=result["error"]
    elif "error" in nested: row["diagnostic"]=nested["error"]
    return row

def _reject(reason:str,result:dict[str,Any],usage:Mapping[str,Any]|None)->dict[str,Any]:
    return {"schema":"golden-v3-result-v2","program_completed":False,"task_success":None,
            "authority_granted":False,"status":"refused","partial_effects":[],"cleanup_error":None,
            "lifecycle":[],"usage":dict(usage if usage is not None else result.get("usage") or {}),
            "adapter_error":reason,"diagnostic":result.get("error"),
            "native_status":None,"raw_dispatch":deepcopy(result)}

def dispatch_golden_v3(program:dict[str,Any],targets:Mapping[str,int],*,current_observation_seq:int,
                       current_binding_revision:int,display_name:str|None=None,
                       usage:Mapping[str,Any]|None=None,
                       capture_directory:str|None=None)->dict[str,Any]:
    options = {} if capture_directory is None else {"capture_directory": capture_directory}
    raw=dispatch(program,targets,current_observation_seq=current_observation_seq,
                 current_binding_revision=current_binding_revision,display_name=display_name, **options)
    return adapt_dispatch_result(raw,usage=usage)
