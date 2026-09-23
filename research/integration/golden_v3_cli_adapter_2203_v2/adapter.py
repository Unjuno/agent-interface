from __future__ import annotations
from typing import Any

STATUSES={"invalid_request","backend_unavailable","runtime_failed","returned"}
LIFECYCLE={"doctor","model_attempt","observation","dispatch","refusal","effect","repair","release","cleanup"}

def adapt_dispatch(result:dict[str,Any], *, usage:dict[str,Any]|None=None, lifecycle:list[str]|None=None)->dict[str,Any]:
    status=result.get("status")
    supplied=list(lifecycle) if lifecycle is not None else ["dispatch"]
    bad_lifecycle=[x for x in supplied if x not in LIFECYCLE]
    if status not in STATUSES:
        return _rejected("UNKNOWN_STATUS",result,usage,supplied,bad_lifecycle)
    if bad_lifecycle:
        return _rejected("UNKNOWN_LIFECYCLE",result,usage,supplied,bad_lifecycle)
    cleanup=result.get("cleanup_error")
    nested=result.get("result") if isinstance(result.get("result"),dict) else {}
    if cleanup is not None:
        mapped="cleanup_failed"
    elif status in {"invalid_request","backend_unavailable"}:
        mapped="refused"
    elif status=="runtime_failed":
        mapped="partial"
    else:
        mapped="success" if nested.get("task_success") is True and nested.get("program_completed") is True else "partial"
    row={"schema":"golden-v3-result-v1","program_completed":mapped=="success","task_success":mapped=="success",
         "authority_granted":False,"status":mapped,"partial_effects":nested.get("partial_effects",[]),
         "cleanup_error":cleanup,"lifecycle":supplied,"usage":dict(usage or result.get("usage") or {})}
    if mapped=="cleanup_failed": row["task_success"]=False
    if "error" in result: row["diagnostic"]=result["error"]
    return row

def _rejected(reason:str,result:dict[str,Any],usage:dict[str,Any]|None,lifecycle:list[str],bad:list[str])->dict[str,Any]:
    return {"schema":"golden-v3-result-v1","program_completed":False,"task_success":False,"authority_granted":False,
            "status":"refused","partial_effects":[],"cleanup_error":None,"lifecycle":[],
            "usage":dict(usage or result.get("usage") or {}),"adapter_error":reason,
            "diagnostic":result.get("error"),"rejected_lifecycle":bad}

def oracle(row:dict[str,Any])->bool:
    if row.get("authority_granted") is not False or row.get("schema")!="golden-v3-result-v1": return False
    if row.get("adapter_error") in {"UNKNOWN_STATUS","UNKNOWN_LIFECYCLE"}: return row["status"]=="refused" and row["lifecycle"]==[]
    if row.get("status")=="success": return row["program_completed"] is True and row["task_success"] is True and row["cleanup_error"] is None
    if row.get("status")=="cleanup_failed": return row["task_success"] is False
    return row["status"] in {"partial","refused","stale_invalidated"}
