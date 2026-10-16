"""Authorize an exact overwrite of hidden text only under current scoped authority."""
import copy
import hashlib

from redaction_action_gate_v1 import contains, intersects


def _digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def authorize(proposal, *, expected_text, field_target_box, save_target_box,
              private_redacted_boxes, presented_binding, current_binding,
              mutation_authority):
    if proposal['kind'] == 'stop':
        return {'authorized': False, 'reason': 'planner_requested_stop'}
    proposal_binding = {name: proposal[name] for name in
                        ('observation_id', 'policy_id', 'policy_version')}
    if proposal_binding != presented_binding:
        return {'authorized': False, 'reason': 'proposal_binding_mismatch'}
    if proposal_binding != current_binding:
        return {'authorized': False, 'reason': 'current_binding_mismatch'}
    if proposal['text'] != expected_text:
        return {'authorized': False, 'reason': 'replacement_text_mismatch'}
    if not contains(field_target_box, proposal['field_x'], proposal['field_y']):
        return {'authorized': False, 'reason': 'field_point_outside_target'}
    if not contains(save_target_box, proposal['save_x'], proposal['save_y']):
        return {'authorized': False, 'reason': 'save_point_outside_target'}

    boxes = copy.deepcopy(private_redacted_boxes)
    hidden_target = any(intersects(field_target_box, box) for box in boxes)
    if not hidden_target:
        return {'authorized': False, 'reason': 'authority_requires_redacted_target'}
    required = {
        'kind': 'replace_entire_text_and_save',
        'observation_id': current_binding['observation_id'],
        'policy_id': current_binding['policy_id'],
        'policy_version': current_binding['policy_version'],
        'field_target_box': field_target_box,
        'save_target_box': save_target_box,
        'replacement_text_sha256': _digest(expected_text),
    }
    if mutation_authority != required:
        return {'authorized': False, 'reason': 'mutation_authority_mismatch'}
    if any(contains(box, proposal['save_x'], proposal['save_y']) for box in boxes):
        return {'authorized': False, 'reason': 'save_point_inside_redaction'}
    return {
        'authorized': True,
        'reason': 'authorized_redacted_full_replacement',
        'steps': [
            {'op': 'pointer_click', 'x': proposal['field_x'],
             'y': proposal['field_y'], 'duration_ms': 80},
            {'op': 'chord', 'modifier': 'Control_L', 'key': 'a'},
            {'op': 'text', 'text': expected_text},
            {'op': 'pointer_click', 'x': proposal['save_x'],
             'y': proposal['save_y'], 'duration_ms': 80},
            {'op': 'observe'},
        ],
    }
