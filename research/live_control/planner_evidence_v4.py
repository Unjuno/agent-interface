"""Strict planner evidence with explicit durable journal revision provenance."""
import copy
import json

from checkpoint_contract_v1 import canonical, validate as validate_contract
from planner_evidence_v2 import checkpoint


SUPPORTED_JOURNALS = ('durable-submit-v4', 'durable-submit-v5', 'durable-submit-v6')


def execution(report):
    if (type(report) is not dict or report.get('format') != 'phased-submit-v1' or
            report.get('authority') != 'none' or type(report.get('exchanges')) is not list):
        raise ValueError('validated phased report required')
    programs = []
    for result in report['exchanges']:
        state, request = result.get('state'), result.get('request')
        if (type(state) is not dict or state.get('format') not in SUPPORTED_JOURNALS or
                state.get('authority') != 'none' or type(request) is not dict):
            raise ValueError('validated durable exchange required')
        command = request.get('command', {})
        if command.get('op') != 'submit' or not any(
                step.get('op') != 'observe' for step in command.get('steps', [])):
            continue
        action_id = command.get('id')
        records = [event for event in result.get('reply', {}).get('records', [])
                   if event.get('id') == action_id]
        accepted = any(event.get('event') == 'accepted' for event in records)
        terminal = (state.get('last_resolution') or {}).get('terminal')
        if not isinstance(action_id, str) or not terminal or terminal.get('id') != action_id:
            raise ValueError('resolved action terminal required')
        release = terminal.get('release') or {}
        released = (release.get('verified') is True and release.get('keys_down') == [] and
                    release.get('buttons_down') == [])
        if not accepted or not released:
            raise ValueError('admitted action with empty verified release required')
        programs.append({
            'action_id': action_id, 'journal_format': state['format'],
            'terminal': terminal.get('status'),
            'steps_completed': terminal.get('steps_completed'),
            'steps_total': len(command['steps']), 'release_empty': True,
            'application_effect': 'unknown',
        })
    if not programs:
        raise ValueError('input program evidence required')
    return {
        'format': 'planner-execution-v2',
        'disposition': report.get('reason') or report.get('status'),
        'programs': programs, 'tail_submitted': report.get('tail_submitted'),
        'new_input': 'requires_new_decision_and_fresh_admission',
        'automatic_retry': 'not_authorized', 'task_completion': 'not_scored',
        'authority': 'none',
    }


def present(checkpoint_resolution, *, expected_request_id, expected_contract,
            phase_report=None, prior_steps=None, recovered=False):
    if type(expected_request_id) is not str or not 1 <= len(expected_request_id) <= 256:
        raise ValueError('bounded expected request identity required')
    contract = validate_contract(expected_contract)
    view = {
        'format': 'planner-evidence-v2',
        'checkpoint': checkpoint(checkpoint_resolution),
        'raw_evidence': 'retained_by_caller', 'authority': 'none',
    }
    if phase_report is not None:
        view['execution'] = execution(phase_report)
    if prior_steps is not None:
        encoded = json.dumps(prior_steps, separators=(',', ':'), allow_nan=False)
        if type(prior_steps) is not list or len(prior_steps) > 10 or len(encoded) > 4096:
            raise ValueError('bounded prior steps required')
        view['prior_steps'] = copy.deepcopy(prior_steps)
    if recovered:
        view['delivery'] = {
            'query_reply': 'recovered_by_command_free_original_id_read',
            'query_resent': False,
        }
    if view['checkpoint']['request_id'] != expected_request_id:
        raise ValueError('checkpoint request identity conflict')
    if canonical(view['checkpoint']['contract']) != canonical(contract):
        raise ValueError('checkpoint completion contract conflict')
    view['binding'] = {
        'expected_request_id': expected_request_id,
        'expected_contract': contract,
        'match': 'verified_before_presentation',
    }
    return view
