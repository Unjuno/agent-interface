"""Plain visual batch for the local six-task comparison; no target reuse."""
import math
from runtime.core_v1.contract import SCHEMA_PROGRAM, validate_program


def validate_grounding(source, grounding):
    sequence = grounding.get('source_sequence')
    if type(sequence) is not int or sequence != source['sequence']:
        raise ValueError('grounding source does not match presented source')
    native = source['native']
    for name in ('field_point', 'submit_point'):
        point = grounding.get(name)
        if not isinstance(point, list) or len(point) != 2:
            raise ValueError('two coordinates required')
        for value, limit in zip(point, (native['width'], native['height'])):
            if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value < limit:
                raise ValueError('finite point within displayed frame required')


def build_program(source, grounding, token, task_id, now_ns):
    validate_grounding(source, grounding)
    def click(point):
        return [{'op': 'pointer_move', 'frame': 'screen_physical_px', 'x': point[0], 'y': point[1]},
                {'op': 'pointer_button', 'button': 'left', 'down': True},
                {'op': 'pointer_button', 'button': 'left', 'down': False}]
    program = {
        'schema': SCHEMA_PROGRAM, 'program_id': 'direct-'+task_id,
        'source': {'observation_seq': source['sequence'], 'binding_revision': source['binding_revision']},
        'authority': {'lease_id': 'native-direct-comparison', 'expires_at_ns': now_ns+5_000_000_000},
        'terminal': {'release_all_required': True},
        'ops': [{'op': 'focus', 'target': 'browser'}, *click(grounding['field_point']),
                {'op': 'key_chord', 'keys': ['CTRL', 'A']}, {'op': 'text', 'text': token},
                {'op': 'wait_update', 'timeout_ms': 100}, *click(grounding['submit_point']),
                {'op': 'wait_update', 'timeout_ms': 100}, {'op': 'release_all'}],
    }
    validate_program(program)
    return program
