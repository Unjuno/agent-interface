"""Fail-closed point/target gate backed by the private observation policy."""
import copy


BOX_SEMANTICS = 'LEFT_TOP_INCLUSIVE_RIGHT_BOTTOM_EXCLUSIVE'


def contains(box, x, y):
    left, top, right, bottom = box
    return left <= x < right and top <= y < bottom


def intersects(first, second):
    return (max(first[0], second[0]) < min(first[2], second[2]) and
            max(first[1], second[1]) < min(first[3], second[3]))


def authorize(proposal, *, allowed_target_box, private_redacted_boxes,
              observation_id, current_observation_id):
    if (type(observation_id) is not str or not observation_id or
            observation_id != current_observation_id):
        return {'authorized': False, 'reason': 'observation_identity_mismatch'}
    if type(allowed_target_box) is not list or len(allowed_target_box) != 4 or \
            any(type(item) is not int for item in allowed_target_box):
        raise ValueError('exact integer target box required')
    boxes = copy.deepcopy(private_redacted_boxes)
    if type(boxes) is not list or any(type(box) is not list or len(box) != 4 or
                                      any(type(item) is not int for item in box)
                                      for box in boxes):
        raise ValueError('exact private redaction boxes required')
    if any(intersects(allowed_target_box, box) for box in boxes):
        return {'authorized': False, 'reason': 'target_evidence_intersects_redaction'}
    if proposal['kind'] == 'stop':
        return {'authorized': False, 'reason': 'planner_requested_stop'}
    x, y = proposal['x'], proposal['y']
    if any(contains(box, x, y) for box in boxes):
        return {'authorized': False, 'reason': 'point_inside_redacted_region'}
    if not contains(allowed_target_box, x, y):
        return {'authorized': False, 'reason': 'point_outside_declared_target'}
    return {
        'authorized': True, 'reason': 'visible_disjoint_target',
        'box_semantics': BOX_SEMANTICS,
        'steps': [{'op': 'pointer_click', 'x': x, 'y': y, 'duration_ms': 80},
                  {'op': 'observe'}],
    }

