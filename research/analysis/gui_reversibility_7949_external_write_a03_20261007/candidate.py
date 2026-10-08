"""A03 candidate; deterministic finite replay, standard library only."""
import importlib.util
from pathlib import Path

_source = Path(__file__).parents[1] / "gui_reversibility_7949_external_write_a01_20261007" / "candidate.py"
_spec = importlib.util.spec_from_file_location("a02_candidate_source_reused", _source)
_impl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_impl)

replay = _impl.replay
evaluate = _impl.evaluate


def run(model):
    return [{"case_id": case["id"], **evaluate(case, model)} for case in model["cases"]]
