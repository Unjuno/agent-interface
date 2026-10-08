"""Compact planner view of validated query and execution evidence.

Raw durable/phased records remain the audit source. This view grants no input
authority and never promotes UNKNOWN or program completion to an app effect.
"""
import copy
import json
from checkpoint_contract_v1 import valid_reply


def checkpoint(resolution):
    if (type(resolution) is not dict or set(resolution) != {'request_id', 'checkpoint', 'authority'} or
            resolution.get('authority') != 'none'):
        raise ValueError('resolved checkpoint evidence required')
    request_id = resolution['request_id']
    record = resolution['checkpoint']
    evidence = record.get('evidence')
    if type(evidence) is not dict or not valid_reply(record, evidence.get('contract'), request_id):
        raise ValueError('invalid checkpoint evidence')
    status = evidence['status']
    result = {'format': 'planner-checkpoint-v1', 'request_id': request_id,
              'status': status, 'contract': copy.deepcopy(evidence['contract']),
              'reason': evidence.get('reason'), 'observation_closed': False,
              'task_completion': 'not_scored', 'authority': 'none',
              'automatic_retry': 'not_authorized'}
    if 'actual' in evidence:
        result['actual'] = copy.deepcopy(evidence['actual'])
    if status == 'VERIFIED':
        result['artifact_sha256'] = evidence['artifact_sha256']
        result['next'] = 'finish_only_if_declared_policy_accepts_this_scope'
    else:
        if evidence.get('error'):
            result['unavailable'] = {'type': evidence['error'].get('type')}
        result['next'] = 'interpret_current_observation_then_require_fresh_admission'
    return result


def execution(report):
    if (type(report) is not dict or report.get('format') != 'phased-submit-v1' or
            report.get('authority') != 'none' or type(report.get('exchanges')) is not list):
        raise ValueError('validated phased report required')
    programs = []
    for result in report['exchanges']:
        state, request = result.get('state'), result.get('request')
        if (type(state) is not dict or state.get('format') not in ('durable-submit-v4', 'durable-submit-v5') or
                state.get('authority') != 'none' or type(request) is not dict):
            raise ValueError('validated durable exchange required')
        command = request.get('command', {})
        if command.get('op') != 'submit' or not any(s.get('op') != 'observe' for s in command.get('steps', [])):
            continue
        action_id = command.get('id')
        records = [event for event in result.get('reply', {}).get('records', []) if event.get('id') == action_id]
        accepted = any(event.get('event') == 'accepted' for event in records)
        terminal = (state.get('last_resolution') or {}).get('terminal')
        if not isinstance(action_id, str) or not terminal or terminal.get('id') != action_id:
            raise ValueError('resolved action terminal required')
        release = terminal.get('release') or {}
        released = (release.get('verified') is True and release.get('keys_down') == [] and
                    release.get('buttons_down') == [])
        if not accepted or not released:
            raise ValueError('admitted action with empty verified release required')
        programs.append({'action_id': action_id, 'terminal': terminal.get('status'),
                         'steps_completed': terminal.get('steps_completed'),
                         'steps_total': len(command['steps']), 'release_empty': True,
                         'application_effect': 'unknown'})
    if not programs:
        raise ValueError('input program evidence required')
    return {'format': 'planner-execution-v1', 'disposition': report.get('reason') or report.get('status'),
            'programs': programs, 'tail_submitted': report.get('tail_submitted'),
            'new_input': 'requires_new_decision_and_fresh_admission',
            'automatic_retry': 'not_authorized', 'task_completion': 'not_scored',
            'authority': 'none'}


def present(checkpoint_resolution, *, phase_report=None, prior_steps=None, recovered=False):
    view = {'format': 'planner-evidence-v1', 'checkpoint': checkpoint(checkpoint_resolution),
            'raw_evidence': 'retained_by_caller', 'authority': 'none'}
    if phase_report is not None:
        view['execution'] = execution(phase_report)
    if prior_steps is not None:
        encoded = json.dumps(prior_steps, separators=(',', ':'), allow_nan=False)
        if type(prior_steps) is not list or len(prior_steps) > 10 or len(encoded) > 4096:
            raise ValueError('bounded prior steps required')
        view['prior_steps'] = copy.deepcopy(prior_steps)
    if recovered:
        view['delivery'] = {'query_reply': 'recovered_by_command_free_original_id_read',
                            'query_resent': False}
    return view
