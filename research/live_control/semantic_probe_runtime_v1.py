"""Backend-independent registry for no-authority exact-frame semantic probes."""
import copy
import time

try:
    from .inkscape_selection_frame_probe_v1 import score_frame
except ImportError:
    from inkscape_selection_frame_probe_v1 import score_frame


class SemanticProbeRegistry:
    def __init__(self):
        self._plans = {}

    def register(self, identifier, plan):
        if not isinstance(identifier, str) or not identifier:
            raise ValueError("nonempty action identifier required")
        if identifier in self._plans:
            raise ValueError("semantic probe already registered")
        if (type(plan) is not dict or
                plan.get("schema") != "inkscape-red-target-plan-v1" or
                plan.get("grants_input_authority") is not False):
            raise ValueError("exact no-authority source plan required")
        self._plans[identifier] = copy.deepcopy(plan)
        return {"schema": "semantic-probe-registration-v1",
                "id": identifier, "status": "REGISTERED_NO_AUTHORITY",
                "grants_input_authority": False}

    def probe(self, identifier, index, sequence, capture_ns, frame):
        plan = self._plans.get(identifier)
        if plan is None:
            return None
        started_ns = time.perf_counter_ns()
        result = score_frame(plan, frame)
        completed_ns = time.perf_counter_ns()
        return {"event": "semantic_probe", "id": identifier, "step": index,
                "sequence": sequence, "capture_ns": capture_ns,
                "probe_started_ns": started_ns,
                "probe_completed_ns": completed_ns,
                "state": "PROVISIONAL_AWAITING_EXACT_ARTIFACT",
                "score": result, "artifact_pending": True,
                "grants_input_authority": False}
