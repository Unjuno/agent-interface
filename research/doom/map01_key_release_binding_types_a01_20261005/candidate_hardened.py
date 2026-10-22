"""Additive guard for malformed key-up identity values in the frozen A01 reducer."""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("frozen_binding_candidate", HERE / "candidate.py")
_FROZEN = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_FROZEN)


def reduce(case):
    for row in case.get("key_ups", []):
        if (not isinstance(row, dict)
                or any(type(row.get(field)) is not str or not row[field]
                       for field in ("admission_id", "execution_id", "key"))):
            return "FAIL", "invalid_up_context_type"
    return _FROZEN.reduce(case)
