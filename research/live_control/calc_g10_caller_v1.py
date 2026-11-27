"""Bind G10-shaped guarded execution to the existing v3 accounting caller.

Callbacks, bridge ownership, target semantics and live deadlines remain caller
responsibilities. No GUI session, target mint or model is started here.
"""
import copy
from research.live_control.adaptive_acquisition_caller_v3 import (
    ExecutionReceiptError, _effect_receipt, run as run_caller,
)
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


def run_g10_in_durable_allocation(spec, caller_adapters, interface_for_target,
                                  bridge, bindings, durable_allocation, *,
                                  perceive, verify_effect, proposal_worker,
                                  cancelled, on_receipt=None, **caller_options):
    """Compose G10 execution with durable all-attempt and effect records.

    The event journal and usage attempt ledger are fsynced as the v3 caller
    advances. The compiled receipt is persisted before the caller's independent
    effect verifier runs. Sink failure remains a caller failure; it cannot
    promote the action or scorer result to task success.
    """
    if type(caller_adapters) is not dict or 'execute' in caller_adapters:
        raise ValueError('caller adapters without execute required')
    if durable_allocation is None or not callable(getattr(durable_allocation, 'append_event', None)):
        raise ValueError('durable allocation ledger required')
    if on_receipt is not None and not callable(on_receipt):
        raise ValueError('optional receipt sink must be callable')
    prior_journal = caller_adapters.get('journal', lambda event: None)
    prior_effect = caller_adapters.get('verify_effect')
    if not callable(prior_journal) or not callable(prior_effect):
        raise ValueError('callable journal and independent effect verifier required')

    adapters = dict(caller_adapters)

    def journal(event):
        durable_allocation.append_event('caller_event', event)
        prior_journal(copy.deepcopy(event))

    def durable_effect(payload):
        raw = prior_effect(copy.deepcopy(payload))
        normalized = _effect_receipt(raw)
        durable_allocation.persist_effect_receipt(normalized)
        return raw

    adapters['journal'] = journal
    adapters['verify_effect'] = durable_effect

    def bound_interface(payload):
        interface = interface_for_target(copy.deepcopy(payload))
        durable_allocation.bind_interface(interface)
        return interface

    def durable_receipt(receipt):
        durable_allocation.persist_execution_receipt(receipt)
        if on_receipt is not None:
            on_receipt(copy.deepcopy(receipt))

    try:
        result = run_g10_in_caller(spec, adapters, bound_interface, bridge,
            bindings, perceive=perceive, verify_effect=verify_effect,
            proposal_worker=proposal_worker, cancelled=cancelled,
            on_receipt=durable_receipt, **caller_options)
    except BaseException as error:
        durable_allocation.record_abort(error)
        raise
    durable_allocation.finalize(result)
    return result
