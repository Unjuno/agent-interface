"""Independent raw-only reconstruction; imports no producer or mechanism."""
import copy
import hashlib
import json
from pathlib import Path
import sys

SCHEMAS = {
    'request': {'caller': str}, 'producer_submitted': {'producer': int},
    'attach': {'caller': str, 'producer': int, 'waiters': int},
    'detach': {'caller': str, 'producer': int, 'waiters': int},
    'worker_enter': {'producer': int, 'active_callables': int},
    'worker_exit': {'producer': int, 'active_callables': int},
    'wrapper_terminal': {'producer': int, 'status': str},
    'future_done': {'producer': int, 'done': bool, 'running': bool},
    'registry_drop': {'producer': int, 'reason': str},
    'caller_deliver': {'caller': str, 'producer': int},
    'caller_cancelled': {'caller': str},
    'caller_yield': {'caller': str, 'reason': str},
    'gate_open': {'producer': int},
    'after_last_detach': {'wrapper_done': bool, 'wrapper_cancelled': bool,
        'future_done': bool, 'future_running': bool, 'active_callables': int,
        'registry_present': bool, 'registry_closing': bool},
    'cleanup': {'active_callables': int, 'wrappers_done': bool, 'futures_done': bool,
        'registry_empty': bool, 'executor_shutdown': bool},
}
SCHEDULES = ('stable_pair', 'one_detach', 'early_rejoin', 'post_exit_rejoin')
POLICIES = ('wrapper_terminal', 'future_ack')


def verify_row(row):
    errors = []
    policy, schedule = row['policy'], row['schedule']
    callers, producers = {}, {}
    registry, closing, active, peak, checkpoints = None, False, 0, 0, 0
    counts = {'delivered': 0, 'cancelled': 0, 'yielded': 0}
    cleanup_seen = False
    for index, event in enumerate(row['events']):
        if type(event) is not dict or type(event.get('event')) is not str or event['event'] not in SCHEMAS:
            errors.append(f'{index}: event schema')
            continue
        kind = event['event']
        schema = dict(sequence=int, event=str, **SCHEMAS[kind])
        if set(event) != set(schema) or any(type(event.get(k)) is not t for k, t in schema.items()):
            errors.append(f'{index}: fields/types')
            continue
        if event['sequence'] != index or cleanup_seen:
            errors.append(f'{index}: order')
        caller, producer = event.get('caller'), event.get('producer')
        if kind == 'request':
            if caller not in ('first', 'second', 'rejoin') or caller in callers:
                errors.append(f'{index}: request identity')
            callers[caller] = {'producer': None, 'outcome': None, 'detached': False}
        elif kind == 'producer_submitted':
            if producer != len(producers) + 1 or registry is not None:
                errors.append(f'{index}: producer/registry')
            producers[producer] = {'entered': False, 'exited': False, 'future_done': False,
                'wrapper': None, 'waiters': 0, 'gate': False}
            registry, closing = producer, False
        elif kind in ('worker_enter', 'worker_exit', 'wrapper_terminal', 'future_done', 'gate_open', 'registry_drop'):
            if producer not in producers:
                errors.append(f'{index}: unknown producer')
                continue
            p = producers[producer]
            if kind == 'worker_enter':
                if p['entered']:
                    errors.append(f'{index}: duplicate enter')
                p['entered'] = True
                active += 1
                peak = max(peak, active)
                if event['active_callables'] != active:
                    errors.append(f'{index}: active enter')
            elif kind == 'worker_exit':
                if not p['entered'] or p['exited'] or not p['gate']:
                    errors.append(f'{index}: exit/gate order')
                p['exited'] = True
                active -= 1
                if event['active_callables'] != active:
                    errors.append(f'{index}: active exit')
            elif kind == 'gate_open':
                if not p['entered'] or p['gate']:
                    errors.append(f'{index}: gate order')
                p['gate'] = True
            elif kind == 'wrapper_terminal':
                if p['wrapper'] is not None or event['status'] not in ('completed', 'cancelled'):
                    errors.append(f'{index}: wrapper status')
                if event['status'] == 'completed' and not p['exited']:
                    errors.append(f'{index}: premature completion')
                if event['status'] == 'cancelled' and p['waiters'] != 0:
                    errors.append(f'{index}: cancellation with attached waiter')
                p['wrapper'] = event['status']
            elif kind == 'future_done':
                if p['future_done'] or not p['exited'] or event['done'] is not True or event['running'] is not False:
                    errors.append(f'{index}: future acknowledgment')
                p['future_done'] = True
            else:
                if registry != producer:
                    errors.append(f'{index}: registry identity')
                if event['reason'] == 'last_detach_wrapper_cancel':
                    if policy != 'wrapper_terminal' or p['waiters'] != 0:
                        errors.append(f'{index}: premature candidate retirement')
                elif event['reason'] == 'future_done':
                    if not p['future_done']:
                        errors.append(f'{index}: retire without acknowledgment')
                elif event['reason'] == 'future_done_observed':
                    if not p['exited']:
                        errors.append(f'{index}: observed done before exit')
                else:
                    errors.append(f'{index}: unknown retirement')
                registry, closing = None, False
        elif kind in ('attach', 'detach', 'caller_deliver', 'caller_cancelled', 'caller_yield'):
            if caller not in callers:
                errors.append(f'{index}: unknown caller')
                continue
            c = callers[caller]
            if kind == 'attach':
                if producer not in producers or registry != producer or closing or c['producer'] is not None:
                    errors.append(f'{index}: invalid attach')
                    continue
                c['producer'] = producer
                producers[producer]['waiters'] += 1
                if event['waiters'] != producers[producer]['waiters']:
                    errors.append(f'{index}: attach count')
            elif kind == 'detach':
                if c['producer'] != producer or c['detached'] or c['outcome'] is None:
                    errors.append(f'{index}: detach identity/order')
                    continue
                c['detached'] = True
                producers[producer]['waiters'] -= 1
                if event['waiters'] != producers[producer]['waiters'] or event['waiters'] < 0:
                    errors.append(f'{index}: detach count')
                if registry == producer and event['waiters'] == 0 and not producers[producer]['exited']:
                    closing = True
            else:
                if c['outcome'] is not None:
                    errors.append(f'{index}: duplicate outcome')
                c['outcome'] = kind
                if kind == 'caller_deliver':
                    if c['producer'] != producer or producer not in producers or not producers[producer]['exited']:
                        errors.append(f'{index}: delivery identity/order')
                    counts['delivered'] += 1
                elif kind == 'caller_cancelled':
                    if c['producer'] is None:
                        errors.append(f'{index}: unattached cancellation')
                    counts['cancelled'] += 1
                else:
                    if c['producer'] is not None or not closing or policy != 'future_ack' or event['reason'] != 'producer_exit_pending':
                        errors.append(f'{index}: yield guard')
                    counts['yielded'] += 1
        elif kind == 'after_last_detach':
            checkpoints += 1
            p = producers.get(1, {})
            if p.get('wrapper') != 'cancelled' or p.get('exited') or active != 1:
                errors.append(f'{index}: checkpoint history')
            expected = dict(wrapper_done=True, wrapper_cancelled=True, future_done=False,
                future_running=True, active_callables=1, registry_present=policy == 'future_ack',
                registry_closing=policy == 'future_ack')
            if any(event[k] != value for k, value in expected.items()) or (registry is not None) != expected['registry_present']:
                errors.append(f'{index}: checkpoint observation')
        elif kind == 'cleanup':
            cleanup_seen = True
            if index != len(row['events'])-1 or active or registry is not None or any(
                not p['exited'] or not p['future_done'] or p['wrapper'] is None or p['waiters'] for p in producers.values()):
                errors.append(f'{index}: incomplete historical cleanup')
            want = dict(active_callables=0, wrappers_done=True, futures_done=True, registry_empty=True, executor_shutdown=True)
            if any(event[k] != v for k, v in want.items()):
                errors.append(f'{index}: cleanup observation')
    want = {
        'stable_pair': (1, 2, 0, 0, 1), 'one_detach': (1, 2, 1, 0, 1),
        'early_rejoin': (1, 0, 2, 1, 1) if policy == 'future_ack' else (2, 1, 2, 0, 2),
        'post_exit_rejoin': (2, 1, 2, 0, 1),
    }[schedule]
    observed = (len(producers), counts['delivered'], counts['cancelled'], counts['yielded'], peak)
    if observed != want or not cleanup_seen or checkpoints != int(schedule in ('early_rejoin', 'post_exit_rejoin')):
        errors.append('schedule/count/cleanup contract')
    expected_callers = {'first', 'second'} if schedule == 'stable_pair' else {'first', 'second', 'rejoin'}
    if set(callers) != expected_callers or any(c['outcome'] is None or (c['producer'] is not None and not c['detached']) for c in callers.values()):
        errors.append('caller coverage')
    return errors, dict(zip(('source_calls', 'delivered', 'cancelled', 'yielded', 'peak_active'), observed))


def verify(data, freeze_bytes):
    errors, summaries, seen = [], [], set()
    keys = {'schema', 'freeze_sha256', 'start_utc', 'end_utc', 'python', 'platform', 'rows', 'formal_allocation'}
    if type(data) is not dict or set(data) != keys or type(data.get('rows')) is not list:
        return {'errors': ['root schema'], 'disposition': 'HOLD'}
    if data['formal_allocation'] is not False or data['schema'] != 'singleflight-thread-exit-v1' or data['freeze_sha256'] != hashlib.sha256(freeze_bytes).hexdigest():
        errors.append('provenance')
    for field in ('start_utc', 'end_utc', 'python', 'platform'):
        if type(data[field]) is not str or not data[field]:
            errors.append('environment/UTC type')
    if data['python'] != json.loads(freeze_bytes)['python']:
        errors.append('interpreter')
    for row in data['rows']:
        if type(row) is not dict or set(row) != {'policy', 'schedule', 'events'} or type(row.get('policy')) is not str or type(row.get('schedule')) is not str or type(row.get('events')) is not list:
            errors.append('row schema')
            continue
        key = row['policy'], row['schedule']
        if key[0] not in POLICIES or key[1] not in SCHEDULES or key in seen:
            errors.append('row coverage')
            continue
        seen.add(key)
        row_errors, summary = verify_row(row)
        errors.extend(f'{key}: {error}' for error in row_errors)
        summaries.append(dict(policy=key[0], schedule=key[1], **summary))
    if seen != {(p, s) for p in POLICIES for s in SCHEDULES} or len(data['rows']) != 8:
        errors.append('denominator')
    return {'disposition': 'HOLD' if errors else 'PASS_THREAD_LIFETIME_SCOPED', 'errors': errors,
        'rows': len(data['rows']), 'summaries': summaries, 'product_or_safety_pass': False}


def mutation_controls(data, freeze):
    def change_checkpoint(d):
        event = next(e for e in d['rows'][2]['events'] if e['event'] == 'after_last_detach')
        event['future_done'] = True
    controls = [lambda d: d['rows'].pop(), lambda d: d['rows'].append(copy.deepcopy(d['rows'][0])),
        lambda d: d['rows'][0]['events'][0].update(sequence=False),
        lambda d: d['rows'][0]['events'][-1].update(executor_shutdown=False), change_checkpoint,
        lambda d: d['rows'][0]['events'][0].update(caller='not-declared'),
        lambda d: d.update(freeze_sha256='0'*64),
        lambda d: d['rows'][0]['events'].pop(2)]
    results = []
    for mutate in controls:
        altered = copy.deepcopy(data)
        mutate(altered)
        results.append(bool(verify(altered, freeze)['errors']))
    return results


def main():
    root = Path(__file__).resolve().parent
    freeze = (root / 'FREEZE.json').read_bytes()
    data = json.loads(Path(sys.argv[1]).read_bytes())
    result = verify(data, freeze)
    for path, digest in json.loads(freeze)['files'].items():
        if hashlib.sha256((root/path).read_bytes()).hexdigest() != digest:
            result['errors'].append('source mismatch: ' + path)
    result['corruptions_rejected'] = mutation_controls(data, freeze)
    if not all(result['corruptions_rejected']):
        result['errors'].append('ineffective corruption control')
    result['disposition'] = 'HOLD' if result['errors'] else 'PASS_THREAD_LIFETIME_SCOPED'
    result['raw_sha256'] = hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest()
    with Path(sys.argv[2]).open('x', encoding='utf-8', newline='\n') as output:
        json.dump(result, output, indent=2)
        output.write('\n')
    print(json.dumps(result))
    sys.exit(bool(result['errors']))

if __name__ == '__main__':
    main()
