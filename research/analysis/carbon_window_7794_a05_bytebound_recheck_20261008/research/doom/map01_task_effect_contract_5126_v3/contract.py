"""V3 candidate: preserve source-collision vs duplicate-effect taxonomy."""
import importlib.util
from pathlib import Path

_SOURCE = Path(__file__).resolve().parents[1] / "map01_task_effect_contract_5126_v2" / "contract.py"
_SPEC = importlib.util.spec_from_file_location("map01_contract_5126_v2_core", _SOURCE)
_CORE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_CORE)


def classify(row):
    result = _CORE.classify(row)
    if result.get("task_effect") == "UNRESOLVED_DUPLICATE_SOURCE_EVENT":
        physical = row.get("physical") or {}
        down, up = physical.get("down") or {}, physical.get("up") or {}
        edge_ids = (down.get("source_event_id"), up.get("source_event_id"))
        scorer_ids = [event.get("source_event_id") for event in row.get("task_effects", [])]
        cross_plane = any(source_id in edge_ids for source_id in scorer_ids)
        if not cross_plane:
            result["task_effect"] = "UNRESOLVED_DUPLICATE_EFFECT"
    return result
