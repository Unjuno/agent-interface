"""Explicit compiled-core composition with the adaptive v3 caller.

Legacy v1 keeps its v2 contract. This entry requires a v3 spec/adapters and
retains the actual returned core receipt separately from the outer task result.
"""
import copy

from research.live_control.adaptive_acquisition_caller_v3 import (
    ExecutionReceiptError, run as run_caller,
)
from runtime.core_v1.compiled_gui import run as run_compiled


def execute_compiled_interface(interface, adapters):
    receipt = run_compiled(interface, adapters)
    if receipt['outcome'] == 'TASK_SUCCEEDED':
        return {'status': 'completed'}, receipt

    decision = {'status': 'safe_yield',
        'reason': receipt['reason'] if receipt['outcome'] == 'SAFE_YIELD' else 'execution_failed',
        'completed_actions': receipt['completed_transitions']}
    terminals = [event for event in receipt['critical_events']
                 if event['event'] == 'action_terminal']
    if receipt['completed_transitions'] or any(e.get('input_dispatched') is True for e in terminals):
        decision['input_dispatched'] = True
    elif all(e.get('input_dispatched') is False for e in terminals):
        # No returned input terminal means execution was never reached. An
        # explicit pre-input refusal is also distinct from unknown delivery.
        decision['input_dispatched'] = False
    return decision, receipt


def run_compiled_interface_in_caller(spec, caller_adapters, interface,
                                     execution_adapters, *, on_receipt=None,
                                     **caller_options):
    """Return v3 caller outcome plus detached compiled receipt/publication error.

    The sink still runs before outer verification. Sink failure skips that
    verifier and remains CALLER_FAILED, without erasing known input progress.
    The returned in-memory receipt is not a durability or release guarantee.
    """
    if type(caller_adapters) is not dict:
        raise ValueError('caller adapter mapping required')
    if 'execute' in caller_adapters:
        raise ValueError('caller execute adapter is supplied by this composition')
    if on_receipt is not None and not callable(on_receipt):
        raise ValueError('on_receipt must be callable')
    retained_receipt = None
    publication_error = None

    def execute(_payload):
        nonlocal retained_receipt, publication_error
        decision, receipt = execute_compiled_interface(interface, execution_adapters)
        retained_receipt = copy.deepcopy(receipt)
        if on_receipt is not None:
            try:
                on_receipt(copy.deepcopy(receipt))
            except Exception as error:
                wrapped = ExecutionReceiptError(decision, error)
                publication_error = {'type': type(error).__name__, 'error': str(wrapped)}
                raise wrapped from error
        return decision

    adapters = dict(caller_adapters, execute=execute)
    result = run_caller(spec, adapters, **caller_options)
    result['compiled_execution_receipt'] = retained_receipt
    result['compiled_receipt_publication_error'] = publication_error
    return result
