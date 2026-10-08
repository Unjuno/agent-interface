"""Read-only completion join for a trusted, stable local publication.

A research contract, NOT a deployed broker or authorization source. No waiting,
request publication, retry, subprocess, model, GUI or task execution occurs here.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import sys

LIMIT = 65536
SEAL_KEYS = {'version', 'request_id', 'request_sha256', 'response_sha256',
             'receipt_sha256', 'broker_process_exit', 'authority_granted'}


def strict_json(raw: bytes) -> object:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate key')
            result[key] = value
        return result
    def reject(_):
        raise ValueError('nonfinite JSON')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=reject)


def read_bounded(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError('not an ordinary retained file')
    with path.open('rb') as stream:
        raw = stream.read(LIMIT + 1)
    if len(raw) > LIMIT:
        raise ValueError('oversized evidence')
    return raw


def collect(ipc: Path, rid: str) -> dict:
    def result(status, **extra):
        return {'status': status, 'request_id': rid, 'authority_granted': False,
                'dispatch_allowed': False, **extra}
    if not re.fullmatch(r'[0-9a-f]{32}', rid):
        return result('REFUSE_ID')
    seal_path = ipc / (rid + '.completion.json')
    if not seal_path.exists():
        return result('PENDING_COMPLETION')
    try:
        seal_raw = read_bounded(seal_path)
        seal = strict_json(seal_raw)
        if not isinstance(seal, dict) or set(seal) != SEAL_KEYS:
            return result('REFUSE_SEAL')
        if type(seal['version']) is not int or seal['version'] != 1:
            return result('REFUSE_TYPES')
        if type(seal['broker_process_exit']) is not int:
            return result('REFUSE_TYPES')
        if seal['authority_granted'] is not False:
            return result('REFUSE_AUTHORITY')
        if seal['request_id'] != rid:
            return result('REFUSE_BINDING')
        raw = {}
        for role, suffix in [('request', '.request.json'), ('response', '.response.jsonl'),
                             ('receipt', '.broker.json')]:
            value = read_bounded(ipc / (rid + suffix))
            expected = seal[role + '_sha256']
            if not isinstance(expected, str) or not re.fullmatch(r'[0-9a-f]{64}', expected):
                return result('REFUSE_BINDING')
            if hashlib.sha256(value).hexdigest() != expected:
                return result('REFUSE_BINDING')
            raw[role] = value
        # Detect a visible seal replacement; stable publication remains an assumption.
        if read_bounded(seal_path) != seal_raw:
            return result('HOLD_CHANGED_PUBLICATION')
        request, receipt = strict_json(raw['request']), strict_json(raw['receipt'])
        if not isinstance(request, dict) or not isinstance(receipt, dict):
            return result('REFUSE_TYPES')
        if request.get('request_id') != rid or receipt.get('request_id') != rid:
            return result('REFUSE_BINDING')
        if request.get('authority_granted') is not False or receipt.get('authority_granted') is not False:
            return result('REFUSE_AUTHORITY')
        if type(receipt.get('returncode')) is not int:
            return result('REFUSE_TYPES')
        if receipt['returncode'] != 0:
            return result('REFUSE_CHILD_EXIT')
        if seal['broker_process_exit'] != 0:
            return result('HOLD_TRANSPORT_EXIT')
        events = [strict_json(x) for x in raw['response'].splitlines() if x.strip()]
        if any(not isinstance(x, dict) for x in events):
            return result('REFUSE_RESPONSE')
        turns = [x for x in events if x.get('type') == 'turn.completed']
        messages = [x for x in events if x.get('type') == 'item.completed']
        if len(turns) != 1 or len(messages) != 1:
            return result('REFUSE_RESPONSE')
        item = messages[0].get('item', {})
        if not isinstance(item, dict) or item.get('type') != 'agent_message' or not isinstance(item.get('text'), str):
            return result('REFUSE_RESPONSE')
        usage = turns[0].get('usage')
        if not isinstance(usage, dict) or any(type(usage.get(k)) is not int or usage[k] < 0
                    for k in ('input_tokens', 'output_tokens')):
            return result('REFUSE_RESPONSE')
        return result('RESULT_AVAILABLE', response_sha256=seal['response_sha256'],
                      result_text=item['text'], usage=usage)
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        return result('REFUSE_EVIDENCE')


if __name__ == '__main__':
    answer = collect(Path(sys.argv[1]), sys.argv[2])
    print(json.dumps(answer, sort_keys=True))
    # Collection itself completed, including explicit pending/refusal. Not task success.
