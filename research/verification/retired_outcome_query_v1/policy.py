"""Read-only reporting policy, not an action-admission or authentication service."""
from typing import Any

FIELDS = {'session', 'resource', 'epoch', 'op_id', 'delta'}

def valid_request(q: Any) -> bool:
    return (type(q) is dict and set(q) == FIELDS
            and all(type(q[k]) is str and 0 < len(q[k]) <= 64
                    for k in ('session', 'resource', 'op_id'))
            and type(q['epoch']) is int and 0 < q['epoch'] < 2**63
            and type(q['delta']) is int and 0 < q['delta'] <= 9)


def classify(packet: Any, expected: Any, policy: str) -> dict:
    """Only a missing current-coverage outcome is eligible for this fixture's retry."""
    if policy not in ('LOOKUP_ONLY', 'COVERAGE_AWARE'):
        raise ValueError('unknown policy')
    def answer(status: str) -> dict:
        return {'status': status, 'submit': status == 'NOT_FOUND_CURRENT',
                'authority': 'none', 'input_dispatched': False}
    if not valid_request(expected):
        return answer('REFUSE_REQUEST')
    if (type(packet) is not dict or set(packet) !=
            {'request', 'scope', 'coverage_epoch', 'receipt', 'authority', 'input_dispatched'}
            or packet['request'] != expected or not valid_request(packet['request'])
            or packet['authority'] != 'none' or packet['input_dispatched'] is not False
            or type(packet['coverage_epoch']) is not int
            or not 0 < packet['coverage_epoch'] < 2**63):
        return answer('REFUSE_PACKET')
    if packet['scope'] != {'session': expected['session'], 'resource': expected['resource']}:
        return answer('REFUSE_SCOPE')
    epoch = packet['coverage_epoch']
    if expected['epoch'] > epoch:
        return answer('REFUSE_FUTURE_EPOCH')
    receipt = packet['receipt']
    if receipt is not None:
        if (type(receipt) is not dict or set(receipt) != {'request', 'status'}
                or not valid_request(receipt['request']) or receipt['status'] != 'COMPLETED'
                or receipt['request']['epoch'] != epoch):
            return answer('REFUSE_RECEIPT')
        if receipt['request'] != expected:
            return answer('CONFLICT_CONTENT')
        return answer('COMPLETED')
    if policy == 'COVERAGE_AWARE' and expected['epoch'] < epoch:
        return answer('OUTCOME_UNKNOWN_RETIRED')
    return answer('NOT_FOUND_CURRENT')
