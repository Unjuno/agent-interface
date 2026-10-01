"""V4 candidate wrapper over the separately frozen v3 classifier."""
import importlib.util
from pathlib import Path

_SOURCE = Path(__file__).resolve().parents[1] / "map01_task_effect_contract_5126_v3" / "contract.py"
_SPEC = importlib.util.spec_from_file_location("map01_contract_5126_v3_core", _SOURCE)
_CORE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_CORE)


def classify(row):
    return _CORE.classify(row)
