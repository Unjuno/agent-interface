"""Authorize a complete field replacement only with visible target evidence."""
import copy

from redaction_action_gate_v1 import contains, intersects


def authorize(proposal, *, expected_text, field_target_box, save_target_box,
              private_redacted_boxes, observation_id, current_observation_id):
    if (type(observation_id) is not str or not observation_id or
            observation_id != current_observation_id):
        return {'authorized': False, 'reason': 'observation_identity_mismatch'}
    boxes = copy.deepcopy(private_redacted_boxes)
    if proposal['kind'] == 'stop':
        return {'authorized': False, 'reason': 'planner_requested_stop'}
    if any(intersects(field_target_box, box) for box in boxes):
        return {'authorized': False,
                'reason': 'required_input_target_intersects_redaction'}
    if any(contains(box, proposal['field_x'], proposal['field_y']) or
           contains(box, proposal['save_x'], proposal['save_y']) for box in boxes):
        return {'authorized': False, 'reason': 'action_point_inside_redaction'}
    if not contains(field_target_box, proposal['field_x'], proposal['field_y']):
        return {'authorized': False, 'reason': 'field_point_outside_target'}
    if not contains(save_target_box, proposal['save_x'], proposal['save_y']):
        return {'authorized': False, 'reason': 'save_point_outside_target'}
    if proposal['text'] != expected_text:
        return {'authorized': False, 'reason': 'replacement_text_mismatch'}
    return {
        'authorized': True, 'reason': 'visible_unredacted_targets',
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
