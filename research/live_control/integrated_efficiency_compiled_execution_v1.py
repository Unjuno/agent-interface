"""Map bounded compiled-GUI receipts to the adaptive caller execution contract."""

from research.live_control.adaptive_acquisition_caller_v2 import run as run_caller
from runtime.core_v1.compiled_gui import run as run_compiled


def execute_compiled_interface(interface, adapters):
    """Run a compiled method and return its typed caller result plus raw receipt.

    The receipt stays available to the composed runner for evidence/accounting.
    A safe yield preserves the completed-transition prefix; only a complete
    compiled method maps to a completed caller execution.
    """
    receipt = run_compiled(interface, adapters)
    if receipt["outcome"] == "TASK_SUCCEEDED":
        decision = {"status": "completed"}
    elif receipt["outcome"] == "SAFE_YIELD":
        decision = {
            "status": "safe_yield",
            "reason": receipt["reason"],
            "completed_actions": receipt["completed_transitions"],
        }
    else:
        decision = {"status": "failed"}
    return decision, receipt


def run_compiled_interface_in_caller(spec, caller_adapters, interface,
                                     execution_adapters, *,
                                     on_receipt=None, **caller_options):
    """Compose a compiled method at the caller's execute stage.

    The compiled runtime's raw receipt can be retained through ``on_receipt``;
    effect verification remains the caller's independent adapter and is only
    reached after the compiled method completes.
    """
    if type(caller_adapters) is not dict:
        raise ValueError("caller adapter mapping required")
    if "execute" in caller_adapters:
        raise ValueError("caller execute adapter is supplied by this composition")
    if on_receipt is not None and not callable(on_receipt):
        raise ValueError("on_receipt must be callable")

    adapters = dict(caller_adapters)

    def execute(_payload):
        decision, receipt = execute_compiled_interface(interface,
                                                       execution_adapters)
        if on_receipt is not None:
            on_receipt(receipt)
        return decision

    adapters["execute"] = execute
    return run_caller(spec, adapters, **caller_options)
