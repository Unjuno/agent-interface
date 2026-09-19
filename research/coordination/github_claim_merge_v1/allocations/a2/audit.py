"""Offline evidence auditor; imports no proposal/controller code; never calls GitHub."""
import hashlib
import json
import re
from pathlib import Path


def require(ok, label):
    if not ok:
        raise ValueError(label)


def serial(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=True) + '\n'


def identity(text):
    raw = text.encode()
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def inspect(plan, records):
    require(len(records) == 3, 'case count')
    outcomes = []
    for spec, row in zip(plan['cases'], records):
        name = spec['name']; require(row['name'] == name, 'case order')
        initial = dict(schema='claim-merge-fixture-v1', case=name, revision=0,
                       claims=[], consumed_task_ids=[], fixture_only=True)
        state = initial
        require(row['initial_read']['content'] == serial(initial), 'initial content')
        require(row['initial_read']['sha'] == identity(serial(initial)), 'initial SHA')
        initial_sha = identity(serial(initial))
        after_a = dict(initial, revision=1, claims=[plan['claims']['A']])
        require(row['recovery_read']['content'] == serial(after_a), 'recovery read')
        require(row['recovery_read']['sha'] == identity(serial(after_a)), 'recovery SHA')
        require([w['step'] for w in row['writes']] == spec['steps'], 'write budget/order')
        for step, success, write in zip(spec['steps'], spec['success'], row['writes']):
            source = initial if step in ('A', 'B_stale') else after_a
            who = 'A' if step == 'A' else ('C' if step == 'C' else spec['candidate'])
            proposed = dict(source, revision=source['revision']+1,
                            claims=source['claims'] + [plan['claims'][who]])
            require(write['content'] == serial(proposed), 'write payload')
            require(write['expected_sha'] == identity(serial(source)), 'write precondition')
            response = write['response']
            if success:
                require(write['expected_sha'] == identity(serial(state)), 'successful current precondition')
                require(response['kind'] == 'success', 'success kind')
                require(re.fullmatch('[0-9a-f]{40}', response['commit_sha']) is not None, 'commit')
                require(response['content_sha'] == identity(write['content']), 'success blob')
                state = proposed
            else:
                require(write['expected_sha'] != identity(serial(state)), 'stale precondition')
                require(response['kind'] == 'error' and response['status'] == 409, 'GitHub 409')
                require(write['expected_sha'] in response['message'] and 'does not match' in response['message'], 'SHA error attribution')
                require(plan['scope'] + 'registers/' + name + '.json' in response['message'], 'error path')
        require(row['terminal'] == spec['expected_terminal'], 'terminal')
        require(row['recovery_policy_status'] == ('CONFLICT' if name == 'duplicate' else 'PROPOSE'), 'policy verdict')
        if name == 'duplicate':
            require(row['recovery_reasons'] == ['semantic_successor'], 'semantic reason')
        require(state['claims'] == [plan['claims'][c] for c in spec['expected_final']], 'final claims')
        require(row['final_read']['content'] == serial(state), 'final exact content')
        require(row['final_read']['sha'] == identity(serial(state)), 'final blob')
        require(row['grants_real_authority'] is False, 'authority')
        outcomes.append({'case': name, 'terminal': row['terminal'], 'writes': len(row['writes']),
                         'final_task_ids': [c['task_id'] for c in state['claims']], 'pass': True})
    return {'decision':'PASS_BOUNDED_CLAIM_MERGE_SCOPED', 'cases':outcomes,
            'limits':'Three sequential prescribed schedules; authored keys; no production or concurrency-rate claim.'}


def main():
    root = Path(__file__).resolve().parent
    freeze = json.loads((root/'freeze.json').read_text())
    for name, h in freeze['source_sha256'].items():
        require(hashlib.sha256((root/name).read_bytes()).hexdigest() == h, 'source hash '+name)
    plan = json.loads((root/'plan.json').read_text())
    records = json.loads((root/'evidence.json').read_text())['cases']
    result = inspect(plan, records)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
