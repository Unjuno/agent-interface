"""Bind G10-shaped guarded execution to the existing v3 accounting caller.

Callbacks, bridge ownership, target semantics and live deadlines remain caller
responsibilities. No GUI session, target mint or model is started here.
"""
import copy
from research.live_control.adaptive_acquisition_caller_v3 import ExecutionReceiptError, run as run_caller
from research.live_control.integrated_efficiency_compiled_execution_v2 import project_compiled_receipt
from research.live_control.calc_g10_fresh_admission_v1 import run_with_bounded_fresh_proposal


def run_g10_in_caller(spec, caller_adapters, interface_for_target, bridge, bindings, *,
                      perceive, verify_effect, proposal_worker, cancelled, on_receipt=None,
                      **caller_options):
    if type(caller_adapters) is not dict or 'execute' in caller_adapters:
        raise ValueError('caller adapters without execute required')
    if not callable(interface_for_target) or (on_receipt is not None and not callable(on_receipt)):
        raise ValueError('target builder and optional receipt sink must be callable')
    retained_receipt = None
    publication_error = None

    def execute(payload):
        nonlocal retained_receipt, publication_error
        graph = interface_for_target(copy.deepcopy(payload))
        receipt = run_with_bounded_fresh_proposal(bridge, graph, bindings,
            perceive=perceive, verify_effect=verify_effect,
            proposal_worker=proposal_worker, cancelled=cancelled)
        retained_receipt = copy.deepcopy(receipt)
        decision = project_compiled_receipt(receipt)
        if on_receipt is not None:
            try:
                on_receipt(copy.deepcopy(receipt))
            except Exception as error:
                wrapped = ExecutionReceiptError(decision, error)
                publication_error = {'type': type(error).__name__, 'error': str(wrapped)}
                raise wrapped from error
        return decision

    result = run_caller(spec, dict(caller_adapters, execute=execute), **caller_options)
    result['compiled_execution_receipt'] = retained_receipt
    result['compiled_receipt_publication_error'] = publication_error
    return result