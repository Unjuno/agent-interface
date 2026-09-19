"""Typed backend-independent semantic probe registry for multiple predicates."""
import copy
import time

try:
    from .exact_crop_semantic_probe_v1 import (CONTRACT_SCHEMA as CROP_CONTRACT,
        SCORE_SCHEMA as CROP_SCORE, reconcile_artifact as reconcile_crop,
        score_frame as score_crop, validate as validate_crop)
    from .inkscape_selection_frame_probe_v1 import (SCHEMA as SELECTION_SCORE,
        reconcile_artifact as reconcile_selection, score_frame as score_selection)
except ImportError:
    from exact_crop_semantic_probe_v1 import (CONTRACT_SCHEMA as CROP_CONTRACT,
        SCORE_SCHEMA as CROP_SCORE, reconcile_artifact as reconcile_crop,
        score_frame as score_crop, validate as validate_crop)
    from inkscape_selection_frame_probe_v1 import (SCHEMA as SELECTION_SCORE,
        reconcile_artifact as reconcile_selection, score_frame as score_selection)


def _validate(contract):
    schema = contract.get("schema") if type(contract) is dict else None
    if schema == "inkscape-red-target-plan-v1":
        if contract.get("grants_input_authority") is not False:
            raise ValueError("selection probe must grant no input authority")
        return copy.deepcopy(contract)
    if schema == CROP_CONTRACT:
        return validate_crop(contract)
    raise ValueError("unsupported typed semantic probe")


def _score(contract, frame):
    return (score_selection(contract, frame) if
            contract["schema"] == "inkscape-red-target-plan-v1" else
            score_crop(contract, frame))


def reconcile_probe_artifact(result, image_path):
    schema = result.get("schema") if type(result) is dict else None
    if schema == SELECTION_SCORE:
        return reconcile_selection(result, image_path)
    if schema == CROP_SCORE:
        return reconcile_crop(result, image_path)
    raise ValueError("unsupported semantic probe result")


class SemanticProbeRegistry:
    def __init__(self):
        self._contracts = {}

    def register(self, identifier, contract):
        if not isinstance(identifier, str) or not identifier:
            raise ValueError("nonempty action identifier required")
        if identifier in self._contracts:
            raise ValueError("semantic probe already registered")
        self._contracts[identifier] = _validate(contract)
        return {"schema": "typed-semantic-probe-registration-v2",
                "id": identifier, "contract_schema": contract["schema"],
                "status": "REGISTERED_NO_AUTHORITY",
                "grants_input_authority": False}

    def probe(self, identifier, index, sequence, capture_ns, frame):
        contract = self._contracts.get(identifier)
        if contract is None:
            return None
        started_ns = time.perf_counter_ns()
        result = _score(contract, frame)
        completed_ns = time.perf_counter_ns()
        return {"event": "semantic_probe", "id": identifier, "step": index,
                "sequence": sequence, "capture_ns": capture_ns,
                "probe_started_ns": started_ns, "probe_completed_ns": completed_ns,
                "state": "PROVISIONAL_AWAITING_EXACT_ARTIFACT", "score": result,
                "artifact_pending": True, "grants_input_authority": False}
