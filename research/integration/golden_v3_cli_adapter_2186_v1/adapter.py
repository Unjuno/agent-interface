"""Authority-neutral adapter from cli_v1 dispatch results to golden-v3 result schema."""
from __future__ import annotations
from typing import Any

LIFECYCLE=("doctor","model_attempt","observation","dispatch","refusal","effect","repair","release","cleanup")

def adapt_dispatch(result: dict[str, Any], *, usage: dict[str, Any] | None = None, lifecycle: list[str] | None = None) -> dict[str, Any]:
    status=result.get("status")
    if status=="invalid_request":
        mapped="refused"
    elif status=="backend_unavailable":
        mapped="refused"
    elif status=="runtime_failed":
        mapped="cleanup_failed" if result.get("cleanup_error") else "partial"
    elif status=="returned":
        nested=result.get("result") or {}
        mapped="success" if nested.get("task_success") is True and nested.get("program_completed") is True else "partial"
    else:
        mapped="partial"
    cleanup_error=result.get("cleanup_error")
    task_success=mapped=="success" and cleanup_error is None
    return {
      "schema":"golden-v3-result-v1",
      "program_completed": mapped=="success",
      "task_success": task_success,
      "authority_granted": False,
      "status": mapped,
      "partial_effects": (result.get("result") or {}).get("partial_effects", []),
      "cleanup_error": cleanup_error,
      "lifecycle": list(lifecycle or (["dispatch","refusal"] if mapped=="refused" else ["dispatch","effect","release","cleanup"])),
      "usage": dict(usage or {}),
    }
