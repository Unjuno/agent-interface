"""Planner evidence bound to the caller's expected query and completion contract.

V2 validates a checkpoint against the contract carried by that checkpoint.  V3
also requires the caller to state what it was waiting for.  A valid but unrelated
checkpoint therefore cannot become model-visible evidence for this decision.
"""
import copy
from checkpoint_contract_v1 import canonical, validate as validate_contract
from planner_evidence_v2 import present as present_v2


def present(checkpoint_resolution, *, expected_request_id, expected_contract,
            phase_report=None, prior_steps=None, recovered=False):
    if type(expected_request_id) is not str or not 1 <= len(expected_request_id) <= 256:
        raise ValueError('bounded expected request identity required')
    contract = validate_contract(expected_contract)
    view = present_v2(checkpoint_resolution, phase_report=phase_report,
                      prior_steps=prior_steps, recovered=recovered)
    checkpoint = view['checkpoint']
    if checkpoint['request_id'] != expected_request_id:
        raise ValueError('checkpoint request identity conflict')
    if canonical(checkpoint['contract']) != canonical(contract):
        raise ValueError('checkpoint completion contract conflict')
    result = copy.deepcopy(view)
    result['binding'] = {
        'expected_request_id': expected_request_id,
        'expected_contract': contract,
        'match': 'verified_before_presentation',
    }
    return result
