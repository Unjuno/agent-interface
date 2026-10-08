"""No-authority readiness receipt for coherent pointer input binding."""
import copy


SCHEMA = "pointer-binding-readiness-v1"


def evaluate(observation, evaluated_ns):
    if type(observation) is not dict or type(evaluated_ns) is not int:
        raise ValueError("observation and evaluation clock required")
    binding = observation.get("pointer_binding")
    before, after = observation.get("pointer_context_before"), observation.get("pointer_context_after")
    ready = (type(binding) is dict and binding == before == after and
        binding.get("focus") not in (None, 0, 1) and
        binding.get("surface") not in (None, 0, 1) and
        type(binding.get("geometry")) is list and len(binding["geometry"]) == 4 and
        all(type(value) is int for value in binding["geometry"]) and
        binding["geometry"][2] > 0 and binding["geometry"][3] > 0 and
        observation.get("focus_samples_match") is True and
        type(observation.get("capture_ns")) is int and
        evaluated_ns >= observation["capture_ns"])
    return {"schema": SCHEMA, "status": "READY" if ready else "WAIT_FOR_COHERENT_BINDING",
        "observation_id": observation.get("id"), "sequence": observation.get("sequence"),
        "binding": copy.deepcopy(binding), "before": copy.deepcopy(before),
        "after": copy.deepcopy(after), "evaluated_ns": evaluated_ns,
        "may_submit_pointer_input": ready, "grants_input_authority": False}
