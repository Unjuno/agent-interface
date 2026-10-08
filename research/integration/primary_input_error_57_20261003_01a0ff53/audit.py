"""Standalone raw-only typed lifecycle reconstruction, no producer/runtime imports."""
import copy, datetime, hashlib, json, pathlib, sys

SCENARIOS = ['before_request', 'pending_success', 'pending_failure', 'eof_pending']
def require(value, message):
    if not value:
        raise ValueError(message)
def same(a, b):
    if type(a) is not type(b):
        return False
    if type(a) is dict:
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if type(a) is list:
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b
def utc(value):
    return datetime.datetime.fromisoformat(value)
def audit(raw):
    require(raw['schema'] == 'primary-read-error-comparison-v1', 'schema')
    require(same(raw['attempts'], 1) and same(raw['retries'], 0), 'invocation count')
    require(raw['node_version'] == 'v26.7.0' and same(raw['scenarios'], SCENARIOS), 'declared environment/deck')
    require(utc(raw['ended_utc']) >= utc(raw['started_utc']), 'run UTC order')
    expected_keys = [(arm, scenario) for arm in ('baseline', 'candidate') for scenario in SCENARIOS]
    require([(r['arm'], r['scenario']) for r in raw['rows']] == expected_keys, 'complete ordered eight-row denominator')
    results = []
    for row in raw['rows']:
        arm, scenario = row['arm'], row['scenario']
        require(utc(row['ended_utc']) >= utc(row['started_utc']), 'child UTC order')
        for channel in ('stdout', 'stderr'):
            require(hashlib.sha256(row[channel].encode()).hexdigest() == row[channel + '_sha256'], 'channel bytes/hash')
        events = [json.loads(line) for line in row['stdout'].splitlines()]
        kinds = [event['kind'] for event in events]
        pending = scenario != 'before_request'
        prefix = ['execute_enter'] if pending else []
        signal = 'eof_issued' if scenario == 'eof_pending' else 'input_error_issued'
        failed_unhandled = arm == 'baseline' and scenario != 'eof_pending'
        if failed_unhandled:
            require(same(row['exit_code'], 1), 'baseline unhandled exit')
            require(kinds == prefix + [signal], 'baseline terminated before owned observation')
            require("Unhandled 'error' event" in row['stderr'] and "Emitted 'error' event on Interface instance" in row['stderr'] and 'inert input read failure' in row['stderr'], 'actual unhandled Interface diagnostic')
        else:
            require(same(row['exit_code'], 0 if scenario == 'eof_pending' else 2), 'owned exit')
            require(row['stderr'] == '', 'no unhandled child diagnostic')
            if pending:
                owner = 'owner_resolved' if scenario == 'eof_pending' else 'owner_rejected'
                require(kinds == prefix + [signal, 'checkpoint', 'execute_exit', 'response', owner, 'final'], 'pending lifecycle order')
                require(same(events[2], {'kind': 'checkpoint', 'calls': 1, 'completed': 0, 'settled': False}), 'same pending command retained')
                require(same(events[3], {'kind': 'execute_exit', 'outcome': 'rejected' if scenario == 'pending_failure' else 'returned'}), 'observed execute outcome')
                response = events[4]['value']
                if scenario == 'pending_failure':
                    require(same(response, {'schema': 'agent-interface/primary-stdio-v1', 'status': 'command_error', 'error': 'Error: inert command outcome unavailable', 'command_id': 1, 'command_method': 'call', 'replay_allowed': False, 'state': {'next_id': 2}}), 'exact uncertainty/no replay response')
                else:
                    require(same(response, {'schema': 'agent-interface/primary-stdio-v1', 'status': 'returned', 'result': {'id': 1, 'value': 'original result'}}), 'exact original result')
                require(same(events[-1], {'kind': 'final', 'calls': 1, 'completed': 1, 'settled': True}), 'single completed command')
            else:
                require(kinds == [signal, 'owner_rejected', 'checkpoint', 'final'], 'pre-request lifecycle order')
                require(same(events[2], {'kind': 'checkpoint', 'calls': 0, 'completed': 0, 'settled': True}), 'pre-request zero invocation')
                require(same(events[-1], {'kind': 'final', 'calls': 0, 'completed': 0, 'settled': True}), 'pre-request terminal')
            if scenario != 'eof_pending':
                owner_event = next(e for e in events if e['kind'] == 'owner_rejected')
                require(same(owner_event, {'kind': 'owner_rejected', 'message': 'inert input read failure'}), 'original stream error identity')
        if pending:
            require(same(events[0], {'kind': 'execute_enter', 'request': {'id': 1, 'method': 'call', 'args': []}}), 'one original request')
        results.append({'arm': arm, 'scenario': scenario, 'child_exit': row['exit_code'], 'unhandled': failed_unhandled,
                        'execute_entries': kinds.count('execute_enter'), 'execute_exits': kinds.count('execute_exit'), 'responses': kinds.count('response')})
    return results

def mutate_events(row, change):
    events = [json.loads(line) for line in row['stdout'].splitlines()]
    change(events)
    row['stdout'] = ''.join(json.dumps(e, separators=(',', ':')) + '\n' for e in events)
    row['stdout_sha256'] = hashlib.sha256(row['stdout'].encode()).hexdigest()

if __name__ == '__main__':
    raw = json.loads(pathlib.Path(sys.argv[1]).read_bytes())
    results = audit(raw)
    controls = [
        ('missing-row', lambda r: r['rows'].pop()),
        ('float-exit', lambda r: r['rows'][5].update(exit_code=2.0)),
        ('premature-owner', lambda r: mutate_events(r['rows'][5], lambda e: e.insert(2, {'kind': 'owner_rejected', 'message': 'inert input read failure'}))),
        ('missing-original-result', lambda r: mutate_events(r['rows'][5], lambda e: e.pop(4))),
        ('replay-allowed', lambda r: mutate_events(r['rows'][6], lambda e: e[4]['value'].update(replay_allowed=True))),
        ('boolean-command-count', lambda r: mutate_events(r['rows'][5], lambda e: e[-1].update(calls=True))),
        ('lost-completion', lambda r: mutate_events(r['rows'][5], lambda e: e[-1].update(completed=0))),
        ('hidden-unhandled-error', lambda r: r['rows'][0].update(stderr='', stderr_sha256=hashlib.sha256(b'').hexdigest())),
    ]
    tested = []
    for name, change in controls:
        copy_raw = copy.deepcopy(raw); change(copy_raw)
        try:
            audit(copy_raw)
        except ValueError as error:
            tested.append({'control': name, 'result': 'REJECTED', 'reason': str(error)})
        else:
            raise ValueError('false accept: ' + name)
    report = {'result': 'PASS_INPUT_ERROR_OWNER_SCOPED', 'rows': results, 'controls': tested,
              'limits': ['inert Node streams/exchange only', 'no actual relay/native input/release/effect, task or timing benefit', 'no byte-framing/deadline/global resource-bound claim']}
    print(json.dumps(report, sort_keys=True))
