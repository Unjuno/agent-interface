"""One-shot trusted local notification schema; no action or effect authority."""
import json

FIELDS = {'schema', 'session', 'request', 'clock', 'owner_pid',
          'commit_before_ns', 'commit_after_ns', 'producer_stamp_ns', 'payload_sha256'}

def validate(data: bytes, expected: dict) -> dict:
    if type(data) is not bytes or len(data) > 4096 or not data.endswith(b'\n'):
        raise ValueError('incomplete_or_oversize_frame')
    if data.count(b'\n') != 1:
        raise ValueError('not_one_frame')
    def pairs(items):
        result = {}
        for k, v in items:
            if k in result:
                raise ValueError('duplicate_field')
            result[k] = v
        return result
    obj = json.loads(data, object_pairs_hook=pairs)
    if type(obj) is not dict or set(obj) != FIELDS:
        raise ValueError('schema_fields')
    for k in ('schema', 'session', 'request', 'clock', 'owner_pid', 'payload_sha256'):
        if type(obj[k]) is not type(expected[k]) or obj[k] != expected[k]:
            raise ValueError('identity_' + k)
    for k in ('commit_before_ns', 'commit_after_ns', 'producer_stamp_ns'):
        if type(obj[k]) is not int or obj[k] < 0:
            raise ValueError('clock_type_' + k)
    if not (expected['start_ns'] <= obj['commit_before_ns'] <=
            obj['commit_after_ns'] <= obj['producer_stamp_ns']):
        raise ValueError('clock_order')
    return obj

def disposition(observed_ns: int, deadline_ns: int) -> dict:
    if type(observed_ns) is not int or type(deadline_ns) is not int:
        raise ValueError('clock_type')
    return {'observation': 'ON_TIME' if observed_ns <= deadline_ns else 'LATE',
            'input_authority': False, 'retry_authority': False,
            'effect_verified': False, 'task_success': None}
