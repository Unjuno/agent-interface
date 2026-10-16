"""Small review card for a narrowly checked successful servo report; otherwise full receipt."""
import argparse
import json
import math
from pathlib import Path
from decision_receipt_v4 import build as detailed
from decision_receipt_v1 import KNOWN_FIELDS

STATE = set('owner_id revision sample_started_ns sample_finished_ns owned_buttons owned_keycodes physical_pointer_mask pointer focus active_lease_deadline_ns active_lease_time_valid cancel_requested'.split())
BRACKETS = set('input_state_before input_state_after input_state_scope owner_revision_unchanged'.split())
TRACK = set('status error margin rival_error source_observation observation frame_id patch_sha256 box delta error_method'.split())


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def integer(value):
    return type(value) is int


def vector(value, count):
    return isinstance(value, list) and len(value) == count and all(integer(x) for x in value)


def state(value):
    require(isinstance(value, dict) and set(value) == STATE, 'unknown/missing input state fields')
    require(isinstance(value['owner_id'], str) and value['owner_id'], 'owner identity missing')
    require(all(integer(value[k]) for k in ('revision', 'sample_started_ns', 'sample_finished_ns', 'physical_pointer_mask', 'focus')), 'state numeric types')
    require(value['revision'] >= 0 and 0 < value['sample_started_ns'] <= value['sample_finished_ns'], 'state ordering')
    require(vector(value['pointer'], 2) and value['owned_keycodes'] == [], 'pointer-only state required')
    require(value['owned_buttons'] in ([], [1]) and value['physical_pointer_mask'] == (256 if value['owned_buttons'] else 0), 'button state mismatch')
    require(value['cancel_requested'] is False and value['active_lease_time_valid'] is True, 'inactive/cancelled sampled lease')


def compact(report, receipt):
    bound = receipt['program_binding']
    require(bound is not None, 'unverified program binding')
    terminal = bound['terminal']
    require(set(terminal) == set('event id status error steps_completed release interruption decision_reason terminal_ns semantic_completion emit_started_ns'.split()), 'terminal fields changed')
    require(terminal['status'] == 'completed' and terminal['steps_completed'] == 1 and terminal['error'] is None and terminal['interruption'] is None and terminal['decision_reason'] is None, 'non-normal terminal')
    release = terminal['release']
    require(set(release) == set('event reason verified buttons_down keys_down verified_ns valid_until_ns'.split()), 'release fields changed')
    require(release['verified'] is True and release['reason'] == 'release' and release['keys_down'] == [] and release['buttons_down'] == [], 'release not verified')
    request = report['exchanges'][1]['request']['command']
    require(len(request['steps']) == 1, 'one servo step required')
    command = request['steps'][0]
    require(set(command) == set('op source_sequence box target_delta points duration_ms max_corrections'.split()) and command['op'] == 'pointer_servo', 'unsupported program')
    require(command['source_sequence'] == report['source_image']['sequence'] and vector(command['target_delta'], 2) and vector(command['box'], 4), 'source/target shape')
    require(integer(command['max_corrections']) and 1 <= command['max_corrections'] <= 3, 'correction bound')
    for item in receipt['attention']:
        require(item['reason'] in ('unknown event fields', 'event requires detail review'), 'negative or unresolved evidence')
        path = item['path']
        require(len(path) == 5 and path[:4] == ['exchanges', 1, 'reply', 'records'], 'attention outside submitted event stream')
    records = report['exchanges'][1]['reply']['records']
    observations, owner, pending, last_feedback = {}, None, None, None
    feedback, corrections, continued = [], 0, 0
    outcomes = []
    for event in records:
        kind = event['event']
        if kind == 'observation':
            require(set(event) <= KNOWN_FIELDS | BRACKETS and BRACKETS <= set(event), 'observation schema')
            require(event['exact'] is True and event['focus_samples_match'] is True and event['owner_revision_unchanged'] is True, 'unstable observation')
            before, after = event['input_state_before'], event['input_state_after']
            state(before); state(after)
            owner = owner or after['owner_id']
            require(before['owner_id'] == after['owner_id'] == owner and before['revision'] == after['revision'], 'owner/revision changed during capture')
            require(before['active_lease_deadline_ns'] == after['active_lease_deadline_ns'] == request['valid_until_ns'], 'lease identity mismatch')
            require(before['sample_finished_ns'] <= event['capture_ns'] <= after['sample_started_ns'], 'capture bracket ordering')
            require(before['focus'] == after['focus'] == event['input_focus_before'] == event['input_focus_after'], 'focus mismatch')
            require(event['pointer_context_before'] == event['pointer_context_after'] == event['pointer_binding'], 'surface mismatch')
            require(integer(event['sequence']) and event['sequence'] > command['source_sequence'] and event['sequence'] not in observations, 'observation sequence')
            observations[event['sequence']] = event
        elif kind == 'pointer_yield':
            require(set(event) == set('event id step update ticket sequence reply_until_ns emit_started_ns'.split()), 'yield schema')
            require(event['id'] == bound['program_id'] and event['step'] == 0 and event['update'] == len(feedback), 'yield attribution/order')
            require(event['sequence'] in observations, 'yield observation missing')
            require(continued == corrections, 'previous correction not acknowledged')
            observed = observations[event['sequence']]
            require(observed['input_state_after']['owned_buttons'] == [1], 'yield without held button')
            require(event['emit_started_ns'] < event['reply_until_ns'] <= request['valid_until_ns'], 'expired yield')
            pending = event
        elif kind == 'servo_feedback':
            require(set(event) == set('event id step observation tracking reason command updates_remaining emit_started_ns'.split()), 'feedback schema')
            require(pending is not None and event['id'] == bound['program_id'] and event['step'] == 0 and event['observation'] == pending['sequence'], 'feedback attribution')
            tracking = event['tracking']
            require(set(tracking) in (TRACK, TRACK | {'raw_error'}), 'tracking schema')
            require(tracking['status'] == 'matched' and tracking['error_method'] in ('raw', 'trimmed_fallback'), 'tracking not matched')
            for key in ('error', 'margin', 'rival_error') + (('raw_error',) if 'raw_error' in tracking else ()):
                require(type(tracking[key]) in (int, float) and math.isfinite(tracking[key]) and 0 <= tracking[key] <= 1, 'invalid tracking metric')
            require(tracking['source_observation'] == command['source_sequence'] and tracking['observation'] == event['observation'] and vector(tracking['delta'], 2) and vector(tracking['box'], 4), 'tracking identity/shape')
            observed = observations[event['observation']]
            require(json.loads(tracking['frame_id']) == observed['pointer_binding'], 'tracking frame mismatch')
            require(tracking['box'] == [command['box'][0] + tracking['delta'][0], command['box'][1] + tracking['delta'][1], *command['box'][2:]], 'tracking box mismatch')
            residual = [a - b for a, b in zip(command['target_delta'], tracking['delta'])]
            if event['reason'] == 'correct':
                require(max(map(abs, residual)) > 1, 'correction contradicts goal')
                point = observed['input_state_after']['pointer']
                expected = {'op': 'move', 'x': point[0] + max(-24, min(24, residual[0])), 'y': point[1] + max(-24, min(24, residual[1]))}
                require(event['command'] == expected, 'correction differs from residual')
                corrections += 1
            else:
                require(event['reason'] == 'local_goal_reached' and event['command'] == {'op': 'finish'} and max(map(abs, residual)) <= 1, 'non-goal or inconsistent outcome')
            require(event['updates_remaining'] == command['max_corrections'] - corrections and corrections <= command['max_corrections'], 'correction accounting')
            require(event['emit_started_ns'] < pending['reply_until_ns'], 'late feedback')
            feedback.append({'sequence': event['observation'], 'delta': tracking['delta'], 'reason': event['reason'], 'distance': tracking['error'], 'method': tracking['error_method']})
            last_feedback = event
        elif kind == 'pointer_admission':
            require(set(event) <= KNOWN_FIELDS | {'continuation', 'owner_id', 'revision'}, 'admission fields')
            if event.get('continuation'):
                require(last_feedback is not None and last_feedback['reason'] == 'correct' and pending is not None, 'unattributed continuation')
                prior = observations[pending['sequence']]['input_state_after']
                require(event['owner_id'] == prior['owner_id'] and event['revision'] == prior['revision'] + 1, 'continuation identity/revision')
                require(event['payload'] == {k: last_feedback['command'][k] for k in ('x', 'y')} and event['admitted_ns'] < pending['reply_until_ns'], 'continuation point/deadline')
                require(event['id'] == bound['program_id'] and event['step'] == 0 and event['valid_until_ns'] == request['valid_until_ns'], 'continuation attribution')
                continued += 1
                last_feedback = None
        elif kind == 'servo_outcome':
            require(set(event) == set('event id step reason local_goal_reached semantic_effect_verified emit_started_ns'.split()), 'outcome schema')
            require(event['reason'] == 'local_goal_reached' and event['local_goal_reached'] is True and event['semantic_effect_verified'] is False, 'non-goal outcome')
            require(event['id'] == bound['program_id'] and event['step'] == 0, 'outcome attribution')
            outcomes.append(event)
        elif kind == 'terminal':
            require(event == terminal, 'terminal mismatch')
        else:
            require(kind in ('command', 'accepted', 'step_started', 'step_completed') and set(event) <= KNOWN_FIELDS, 'unknown event')
    require(len(outcomes) == 1 and feedback and feedback[-1]['reason'] == 'local_goal_reached' and continued == corrections, 'missing goal evidence')
    require(receipt['image']['status'] == 'image', 'no result image')
    return {'format': 'servo-review-v1', 'source': receipt['source'], 'program': bound['program_id'],
            'status': terminal['status'], 'steps_completed': 1, 'target_delta': command['target_delta'],
            'feedback': feedback, 'corrections': corrections, 'release': release, 'image': receipt['image'],
            'interruption': None, 'task_success': 'unknown; independent saved-output scoring required',
            'review_scope': 'selected successful servo fields; full records remain in source; not complete schema validation',
            'authority': 'none; all input-state samples are historical, no renewed lease or approval',
            'detail_review_required': False}


def build(data):
    receipt = detailed(data)
    try:
        return compact(json.loads(data), receipt)
    except (ValueError, TypeError, KeyError, IndexError) as exc:
        receipt['compact_unavailable'] = str(exc)
        receipt['detail_review_required'] = True
        return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    from report_pages_v2 import MAX_SOURCE
    with args.source.open('rb') as stream:
        data = stream.read(MAX_SOURCE + 1)
    print(json.dumps(build(data), allow_nan=False))
