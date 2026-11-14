"""Adapt the retained App Server grounding client to the v3 caller contract."""
from __future__ import annotations

try:
    from .adaptive_acquisition_caller_v3 import ModelFailure
    from .integrated_efficiency_app_server_model_v1 import GroundingCallError
except ImportError:  # Research scripts may place this directory directly on sys.path.
    from adaptive_acquisition_caller_v3 import ModelFailure
    from integrated_efficiency_app_server_model_v1 import GroundingCallError


def _output(result, project):
    value = project(result["grounding"])
    if type(value) is not dict:
        raise ValueError("grounding output projection must return an object")
    return value


class V3PersistentGroundingAdapter:
    """One provider call, projected to the exact v3 result/error envelope.

    No retries are performed. Provider/accounting failures are raised as the
    v3 typed ModelFailure with all metadata already observed by the underlying
    App Server grounding client.
    """
    def __init__(self, model, output_projector=None):
        if not callable(getattr(model, "call", None)):
            raise ValueError("persistent grounding model with callable call required")
        if output_projector is not None and not callable(output_projector):
            raise ValueError("output_projector must be callable")
        self.model = model
        self.output_projector = output_projector or (
            lambda grounding: {"status": "target_reference", "target": grounding})

    def __call__(self, root, prompt, image, contract, workspace):
        try:
            result = self.model.call(root, prompt, image, contract, workspace)
        except GroundingCallError as error:
            raise ModelFailure(str(error), call_id=error.call_id,
                thread_id=error.thread_id, requested_model=error.requested_model,
                requested_effort=error.requested_effort, usage=error.usage,
                visible_images_submitted=error.visible_images_submitted,
                wait_ns=error.wait_ns, cost=None) from error
        required = {"grounding", "call_id", "thread_id", "usage",
                    "requested_model", "requested_effort", "runner_ns"}
        if type(result) is not dict or not required <= set(result):
            raise ValueError("persistent grounding result lacks v3 projection fields")
        try:
            output = _output(result, self.output_projector)
        except Exception as error:
            raise ModelFailure(str(error), call_id=result["call_id"],
                thread_id=result["thread_id"],
                requested_model=result["requested_model"],
                requested_effort=result["requested_effort"],
                usage=result["usage"], visible_images_submitted=1,
                wait_ns=result["runner_ns"], cost=result.get("cost"),
                typed_status="FAILED_OUTPUT") from error
        return {"call_id": result["call_id"], "thread_id": result["thread_id"],
                "output": output,
                "usage": result["usage"],
                "requested_model": result["requested_model"],
                "requested_effort": result["requested_effort"],
                "cost": result.get("cost"),
                "visible_images_submitted": 1,
                "wait_ns": result["runner_ns"]}
