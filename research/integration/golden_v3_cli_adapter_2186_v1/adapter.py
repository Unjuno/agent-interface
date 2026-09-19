"""Authority-neutral adapter from cli_v1 dispatch results to golden-v3 result schema."""
from __future__ import annotations
from typing import Any

def adapt_dispatch(result: dict[str, Any], *, usage: dict[str, Any] | None = None, lifecycle: list[str] | None = None) -> dict[str, Any]:
    status=result.get("status")
    cleanup_error=result.get("cleanup_error")
    if cleanup_error is not None:
        mapped="cleanup_failed"
    elif status in {"invalid_request","backend_unavailable"}:
        mapped="refused"
    elif status=="runtime_failed":
        mapped="partial"
    elif status=="returned":
        nested=result.get("result") or {}
        mapped="success" if nested.get("task_success") is True and nested.get("program_completed") is True else "partial"
    else:
        mapped="partial"
    nested=result.get("result") or {}
    return {
      "schema":"golden-v3-result-v1",
      "program_completed": mapped=="success",
      "task_success": mapped=="success",
      "authority_granted": False,
      "status": mapped,
      "partial_effects": nested.get("partial_effects", []),
      "cleanup_error": cleanup_error,
      "lifecycle": list(lifecycle or (["dispatch","refusal"] if mapped=="refused" else ["dispatch","effect","release","cleanup"])),
      "usage": dict(usage or {}),
    }
