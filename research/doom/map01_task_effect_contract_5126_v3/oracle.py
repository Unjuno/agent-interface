"""Independent reference: derives the identity-collision category from raw rows."""
import importlib.util
from pathlib import Path

_SOURCE = Path(__file__).resolve().parents[1] / "map01_task_effect_contract_5126_v2" / "oracle.py"
_SPEC = importlib.util.spec_from_file_location("map01_oracle_5126_v2_core", _SOURCE)
_CORE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_CORE)


def oracle(record):
    result = _CORE.oracle(record)
    if result.get("task_effect") == "UNRESOLVED_DUPLICATE_SOURCE_EVENT":
        physical = record.get("physical") or {}
        edges = (physical.get("down") or {}, physical.get("up") or {})
        physical_references = tuple(edge.get("source_event_id") for edge in edges)
        score_references = [event.get("source_event_id") for event in record.get("task_effects", [])]
        if not any(ref in physical_references for ref in score_references):
            result["task_effect"] = "UNRESOLVED_DUPLICATE_EFFECT"
    return result
