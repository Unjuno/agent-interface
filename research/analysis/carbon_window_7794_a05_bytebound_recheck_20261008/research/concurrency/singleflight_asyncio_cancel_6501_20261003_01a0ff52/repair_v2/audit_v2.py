"""Retained-raw event reducer; imports no candidate, runtime, or v1 auditor.

The seven review boundaries were identified and independently checked by worker
01a0ff2d-eb8e-70e0-82bb-ba3bf0c79b5c in PR #6890 comments
5964335802/5964353535. This standalone reducer also validates the complete schema,
finite denominator and offered barrier/cancellation conditions.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

ARMS = ('independent', 'direct', 'shield', 'shield_refcount')
CASES = ('stable', 'cancel_first', 'cancel_last', 'cancel_all', 'generation_change', 'owner_failure')
DOMAIN = list(itertools.product((2, 3), CASES, ARMS))
PAYLOAD = hashlib.sha256(b'descriptive-read:surface-A:generation-1').hexdigest()
BASE = {'seq': int, 'actor': str, 'kind': str}
FIELDS = {
    'producer_start': {}, 'producer_exit': {}, 'producer_cancelled': {},
    'producer_return': {'generation': int, 'payload_sha256': str},
    'producer_error': {'error': str}, 'waiter_start': {}, 'waiter_cancelled': {},
    'waiter_error': {'error': str}, 'waiter_detach': {'remaining': int},
    'waiter_result': {'status': str, 'current_generation': int, 'generation': int, 'payload_sha256': str},
    'barrier_ready': {}, 'gate_open': {}, 'generation_change': {'generation': int},
    'cancel_request': {'caller': int}, 'cleanup_cancel': {'producer': str},
    'last_waiter_cancel': {'producer': str},
}


def shape(value, fields):
    return (type(value) is dict and set(value) == set(fields)
            and all(type(value[k]) is t for k, t in fields.items()))


def check(raw):
    errors = []
    try:
        if not shape(raw, {'schema': str, 'python': str, 'platform': str, 'event_loop': str, 'rows': list}):
            return ['schema']
        if raw['schema'] != 'asyncio-singleflight-cancellation-v1' or len(raw['rows']) != len(DOMAIN):
            return ['denominator']
        for row, expected_key in zip(raw['rows'], DOMAIN):
            if not shape(row, {'callers': int, 'scenario': str, 'policy': str, 'events': list,
                               'outcomes': list, 'before_cleanup': list, 'after_cleanup': list}):
                errors.append('row schema')
                continue
            n, case, arm = row['callers'], row['scenario'], row['policy']
            if (n, case, arm) != expected_key:
                errors.append('row denominator/order')
                continue
            label = f'{n}/{case}/{arm}'
            def require(condition, reason):
                if not condition:
                    errors.append(label + ':' + reason)
            events = row['events']
            if not all(type(e) is dict and type(e.get('kind')) is str and e['kind'] in FIELDS
                       and shape(e, BASE | FIELDS[e['kind']]) for e in events):
                errors.append(label + ':event schema')
                continue
            require([e['seq'] for e in events] == list(range(1, len(events) + 1)), 'sequence')
            producers = ['p' + str(i) for i in range(n if arm == 'independent' else 1)]
            waiters = ['w' + str(i) for i in range(n)]
            for e in events:
                actors = producers if e['kind'].startswith('producer_') else waiters if e['kind'].startswith('waiter_') else ['coordinator']
                require(e['actor'] in actors, 'event actor')
            def select(kind, actor=None):
                return [e for e in events if e['kind'] == kind and (actor is None or e['actor'] == actor)]
            barrier = select('barrier_ready')
            if len(barrier) != 1:
                errors.append(label + ':barrier count')
                continue
            barrier_seq = barrier[0]['seq']
            require([e['actor'] for e in select('producer_start')] == producers, 'producer start identities')
            require([e['actor'] for e in select('waiter_start')] == waiters, 'waiter start identities')
            require(all(e['seq'] < barrier_seq for e in events if e['kind'] in ('producer_start', 'waiter_start')), 'ready before barrier')
            cancelled = [0] if case == 'cancel_first' else [n - 1] if case == 'cancel_last' else list(range(n)) if case == 'cancel_all' else []
            requests = select('cancel_request')
            require([e['caller'] for e in requests] == cancelled, 'offered cancellation')
            require(all(e['seq'] > barrier_seq for e in requests), 'cancellation after barrier')
            gates = select('gate_open')
            require(len(gates) == int(case != 'cancel_all'), 'gate count')
            require(all(e['seq'] > barrier_seq and all(c['seq'] < e['seq'] for c in requests) for e in gates), 'gate order')
            changes = select('generation_change')
            require(len(changes) == int(case == 'generation_change'), 'generation-change count')
            require(all(e['generation'] == 2 and barrier_seq < e['seq'] and len(gates) == 1 and e['seq'] < gates[0]['seq'] for e in changes), 'generation-change order/identity')

            # Conservation is reduced from ordered detach events, not copied fields.
            detaches = select('waiter_detach')
            require(len(detaches) == n and {e['actor'] for e in detaches} == set(waiters), 'detach denominator')
            require([e['remaining'] for e in detaches] == list(range(n - 1, -1, -1)), 'detach conservation')
            cleanups = select('cleanup_cancel')
            last = select('last_waiter_cancel')
            pending = case == 'cancel_all' and arm == 'shield'
            require(len(cleanups) == int(pending), 'cleanup count')
            require(len(last) == int(case == 'cancel_all' and arm == 'shield_refcount'), 'last-detach owner count')
            for e in cleanups + last:
                require(e['producer'] == 'p0' and len(detaches) == n and all(d['seq'] < e['seq'] for d in detaches), 'owner cancellation after all detach')
            snapshots = []
            for name in ('before_cleanup', 'after_cleanup'):
                states = row[name]
                if not all(shape(s, {'producer': str, 'done': bool, 'cancelled': bool}) for s in states):
                    errors.append(label + ':task state schema')
                    snapshots.append({})
                    continue
                require([s['producer'] for s in states] == producers, 'task state identities')
                snapshots.append({s['producer']: s for s in states})
            terminal_map = {}
            for index, producer in enumerate(producers):
                starts = select('producer_start', producer)
                terminals = [e for e in events if e['actor'] == producer and e['kind'] in ('producer_return', 'producer_error', 'producer_cancelled')]
                exits = select('producer_exit', producer)
                if not len(starts) == len(terminals) == len(exits) == 1:
                    errors.append(label + ':producer terminal count ' + producer)
                    continue
                t, start, end = terminals[0], starts[0], exits[0]
                was_cancelled = (index in cancelled if arm == 'independent'
                                 else bool(cancelled) and (arm == 'direct' or case == 'cancel_all'))
                expected_terminal = 'producer_cancelled' if was_cancelled else 'producer_error' if case == 'owner_failure' else 'producer_return'
                require(t['kind'] == expected_terminal, 'producer terminal kind ' + producer)
                require(start['seq'] < t['seq'] < end['seq'], 'producer terminal/exit order ' + producer)
                if t['kind'] == 'producer_return':
                    require(t['generation'] == 1 and t['payload_sha256'] == PAYLOAD, 'producer result identity')
                if t['kind'] == 'producer_error':
                    require(t['error'] == 'RuntimeError', 'producer error identity')
                if t['kind'] != 'producer_cancelled':
                    require(len(gates) == 1 and gates[0]['seq'] < t['seq'], 'producer gate order')
                else:
                    causes = ([e for e in requests if e['caller'] == index] if arm == 'independent'
                              else requests if arm == 'direct' else cleanups + last)
                    require(bool(causes) and min(e['seq'] for e in causes) < t['seq'], 'producer cancellation cause')
                for j, states in enumerate(snapshots):
                    state = states.get(producer)
                    require(state is not None, 'state coverage ' + producer)
                    if state is None:
                        continue
                    expected_done = not (j == 0 and pending)
                    require(state['done'] is expected_done and state['cancelled'] is (was_cancelled and expected_done), 'task/terminal reconciliation ' + producer)
                if pending:
                    require(len(cleanups) == 1 and cleanups[0]['seq'] < t['seq'], 'cleanup before producer terminal')
                terminal_map[producer] = (t, end)
            outcomes = row['outcomes']
            if len(outcomes) != n or not all(
                type(o) is dict and set(o) == {'caller', 'status', 'generation', 'payload_sha256'}
                and type(o['caller']) is int and type(o['status']) is str
                and (o['generation'] is None or type(o['generation']) is int)
                and (o['payload_sha256'] is None or type(o['payload_sha256']) is str)
                for o in outcomes
            ):
                errors.append(label + ':outcome schema')
                continue
            require([o['caller'] for o in outcomes] == list(range(n)), 'outcome identities')
            for index, outcome in enumerate(outcomes):
                actor = waiters[index]
                expected_status = ('CANCELLED' if index in cancelled or (cancelled and arm == 'direct') else 'STALE' if case == 'generation_change' else 'OWNER_FAILED' if case == 'owner_failure' else 'DELIVERED')
                require(outcome['status'] == expected_status, 'outcome status ' + actor)
                terminals = [e for e in events if e['actor'] == actor and e['kind'] in ('waiter_result', 'waiter_error', 'waiter_cancelled')]
                detached = select('waiter_detach', actor)
                if len(terminals) != 1 or len(detached) != 1:
                    errors.append(label + ':waiter terminal/detach count ' + actor)
                    continue
                t = terminals[0]
                require(barrier_seq < t['seq'] < detached[0]['seq'], 'waiter terminal before detach ' + actor)
                expected_kind = 'waiter_cancelled' if expected_status == 'CANCELLED' else 'waiter_error' if expected_status == 'OWNER_FAILED' else 'waiter_result'
                require(t['kind'] == expected_kind, 'waiter terminal kind ' + actor)
                producer = 'p' + str(index) if arm == 'independent' else 'p0'
                source = terminal_map.get(producer)
                if expected_kind == 'waiter_result':
                    require(type(outcome['generation']) is int and outcome['generation'] == 1 and type(outcome['payload_sha256']) is str and outcome['payload_sha256'] == PAYLOAD, 'outcome result identity')
                    require(t.get('generation') == outcome['generation'] and t.get('payload_sha256') == outcome['payload_sha256'] and t.get('status') == outcome['status'], 'event/outcome identity')
                    require(t.get('current_generation') == (2 if case == 'generation_change' else 1), 'current generation identity')
                else:
                    require(outcome['generation'] is None and outcome['payload_sha256'] is None, 'non-delivery payload')
                    if expected_kind == 'waiter_error':
                        require(t.get('error') == 'RuntimeError', 'waiter error identity')
                if expected_kind in ('waiter_result', 'waiter_error') or arm in ('independent', 'direct'):
                    require(source is not None and source[1]['seq'] < t['seq'], 'producer exit before waiter terminal')
                if source is not None and expected_kind == 'waiter_result':
                    require(source[0].get('generation') == t.get('generation') and source[0].get('payload_sha256') == t.get('payload_sha256'), 'producer/waiter result identity')
                if index in cancelled:
                    own_requests = [e for e in requests if e['caller'] == index]
                    require(len(own_requests) == 1 and own_requests[0]['seq'] < t['seq'], 'requested waiter cancellation order')
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        errors.append('malformed:' + type(exc).__name__)
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('raw')
    parser.add_argument('--expected-raw-sha256', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    blob = Path(args.raw).read_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    if digest != args.expected_raw_sha256:
        result = {'status': 'STOP_RAW_IDENTITY', 'raw_sha256': digest}
    else:
        try:
            raw = json.loads(blob)
            errors = check(raw)
        except (ValueError, UnicodeError) as exc:
            errors = ['malformed:' + type(exc).__name__]
        result = {'status': 'PASS_RETAINED_TRACE_V2_SCOPED' if not errors else 'FAIL_RETAINED_TRACE_V2',
                  'raw_sha256': digest, 'rows': 48 if not errors else None,
                  'caller_outcomes': 120 if not errors else None, 'errors': errors}
    with Path(args.output).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write('\n')
    print(json.dumps(result, sort_keys=True))
    return int(result['status'] != 'PASS_RETAINED_TRACE_V2_SCOPED')


if __name__ == '__main__':
    raise SystemExit(main())
