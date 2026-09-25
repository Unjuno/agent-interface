"""Finite copied-record audit checks, not runtime fault injection."""
import copy
import hashlib
import json
from pathlib import Path
import sys
from audit_compat import audit


def encode(obj):
    return json.dumps(obj, sort_keys=True).encode()


def main():
    original = json.loads(Path(sys.argv[1]).read_text())
    freeze = Path(sys.argv[2]).read_bytes()
    if audit(original, freeze)['errors']:
        raise ValueError('BASELINE_AUDIT_FAILED')
    cases = []
    for name in ('missing_row', 'duplicate_row', 'boolean_exit', 'payload', 'cursor', 'source', 'input_mutation', 'time_order'):
        changed = copy.deepcopy(original)
        if name == 'missing_row':
            changed['rows'].pop()
        elif name == 'duplicate_row':
            changed['rows'][-1] = copy.deepcopy(changed['rows'][0])
        elif name == 'boolean_exit':
            changed['rows'][0]['exit'] = False
        elif name in ('payload', 'cursor'):
            response = json.loads(changed['rows'][0]['stdout'])
            if name == 'payload':
                response['records'][0]['event'] = 'other'
            else:
                response['next_cursor']['prefix_sha256'] = '0' * 64
            changed['rows'][0]['stdout'] = json.dumps(response) + '\n'
        elif name == 'source':
            changed['sources']['source/candidate_reader.py'] = '0' * 64
        elif name == 'input_mutation':
            changed['rows'][0]['stream_after'] += '20'
        else:
            changed['rows'][0]['end_ns'] = changed['rows'][0]['start_ns'] - 1
        if encode(changed) == encode(original):
            raise ValueError('NO_OP_CONTROL:' + name)
        result = audit(changed, freeze)
        cases.append(dict(name=name, changed_sha256=hashlib.sha256(encode(changed)).hexdigest(),
                          rejected=bool(result['errors']), errors=result['errors']))
    result = dict(status='PASS_CONTROLS' if all(c['rejected'] for c in cases) else 'FAIL_CONTROLS',
                  cases=cases, original_sha256=hashlib.sha256(encode(original)).hexdigest())
    print(json.dumps(result, sort_keys=True))
    return 0 if result['status'] == 'PASS_CONTROLS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
