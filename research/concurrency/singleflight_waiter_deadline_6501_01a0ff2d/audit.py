"""Independent raw-only deadline/event oracle; no candidate/runtime imports."""
import copy
import hashlib
import itertools
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
CANON = lambda v: json.dumps(v, sort_keys=True, separators=(',', ':'), allow_nan=False)

def verify(raw):
    failures = []
    freeze = json.loads((HERE / 'FREEZE.json').read_bytes())
    if raw.get('freeze_sha256') != hashlib.sha256((HERE / 'FREEZE.json').read_bytes()).hexdigest():
        failures.append('freeze_identity')
    if raw.get('source_sha256') != freeze['sha256']['candidate.py']:
        failures.append('source_identity')
    if raw.get('python') != freeze['python'] or raw.get('stdlib_sha256') != freeze['stdlib_sha256']:
        failures.append('runtime_identity')
    if raw.get('backend_opened') is not False or raw.get('input_dispatched') is not False:
        failures.append('authority')
    fixtures = json.loads((HERE / 'fixtures.json').read_bytes())
    rows = raw.get('rows')
    if type(rows) is not list or len(rows) != 30:
        return failures + ['denominator']
    for row, fixture in zip(rows, fixtures):
        label = fixture['id']
        if any(CANON(row.get(k)) != CANON(v) for k, v in fixture.items()):
            failures.append('condition:' + label)
        policy, schedule, suppress = fixture['policy'], fixture['schedule'], fixture['suppress_cancel']
        events = row.get('events', [])
        if not events or any(type(e.get('ns')) is not int or e['ns'] < 0 or type(e.get('seq')) is not int or e.get('seq') != i for i, e in enumerate(events)):
            failures.append('event_shape:' + label)
            continue
        if any(a['ns'] > b['ns'] for a, b in zip(events, events[1:])):
            failures.append('event_clock:' + label)
        names = [e['name'] for e in events]
        required = ['producer_start', 'wait_start', 'timed_decision', 'cleanup_begin', 'cleanup_end']
        if any(names.count(n) != 1 for n in required):
            failures.append('event_cardinality:' + label)
            continue
        by_name = {e['name']: e for e in events}
        if any(n not in set(required + ['producer_cancel', 'producer_return', 'companion_return', 'companion_cancel', 'wait_return']) for n in names):
            failures.append('extra_event:' + label)
        deadline = row.get('deadline_ns')
        timed, peer = row.get('timed', {}), row.get('companion', {})
        if type(deadline) is not int or type(timed.get('decision_ns')) is not int:
            failures.append('deadline_type:' + label)
            continue
        if by_name['wait_start'].get('deadline_ns') != deadline:
            failures.append('deadline_identity:' + label)
        decision = by_name['timed_decision']
        if any(CANON(decision.get(k)) != CANON(v) for k, v in timed.items()) or not deadline >= 0:
            failures.append('decision_event:' + label)
        overdue = schedule in ('preexpired', 'timeout')
        direct_cancel = policy == 'direct' and overdue
        cancelled_owner = direct_cancel and not suppress
        value_returned = not overdue or (direct_cancel and suppress)
        result = 'UNKNOWN' if schedule == 'unknown' else 'READY'
        if 'producer_cancel' in by_name and by_name['producer_cancel'].get('suppress') is not suppress:
            failures.append('cancel_kind:' + label)
        if any(e.get('result') != result for e in events if e['name'] in ('producer_return', 'companion_return', 'wait_return')):
            failures.append('result_identity:' + label)
        expected_terminal = 'value' if value_returned else 'timeout'
        expected_accept = value_returned and result == 'READY' and not (policy == 'shield_deadline' and schedule == 'decision_delay')
        expected_peer = {'terminal': 'cancelled', 'accepted': False} if cancelled_owner else {'terminal': 'value', 'result': result, 'accepted': result == 'READY'}
        if timed.get('terminal') != expected_terminal or timed.get('accepted') is not expected_accept or CANON(peer) != CANON(expected_peer):
            failures.append('outcome:' + label)
        if value_returned and (timed.get('result') != result or names.count('wait_return') != 1):
            failures.append('returned_value:' + label)
        if not value_returned and ('result' in timed or 'wait_return' in names):
            failures.append('timeout_value:' + label)
        if names.count('producer_cancel') != int(direct_cancel) or names.count('producer_return') != int(not cancelled_owner):
            failures.append('producer_terminal:' + label)
        if names.count('companion_cancel') != int(cancelled_owner) or names.count('companion_return') != int(not cancelled_owner):
            failures.append('companion_terminal:' + label)
        if value_returned and names.index('producer_return') >= names.index('wait_return'):
            failures.append('return_order:' + label)
        if schedule in ('fresh', 'unknown') and timed['decision_ns'] >= deadline:
            failures.append('fresh_clock_not_eligible:' + label)
        if value_returned and schedule in ('preexpired', 'timeout', 'decision_delay') and timed['decision_ns'] < deadline:
            failures.append('late_clock_not_eligible:' + label)
        if timed['decision_ns'] > decision['ns'] or decision['ns'] > by_name['cleanup_begin']['ns']:
            failures.append('decision_clock:' + label)
        pending = overdue and policy != 'direct'
        if row.get('pending_before_cleanup') is not pending or by_name['cleanup_begin'].get('pending_producer') is not pending:
            failures.append('pending_owner:' + label)
        if row.get('producer_cancelled') is not cancelled_owner or row.get('all_tasks_terminal') is not True:
            failures.append('cleanup:' + label)
        if by_name['cleanup_end'].get('producer_done') is not True or by_name['cleanup_end'].get('companion_done') is not True:
            failures.append('cleanup_receipt:' + label)
    return failures

if __name__ == '__main__':
    raw = json.loads(Path(sys.argv[1]).read_bytes())
    errors = verify(raw)
    controls = []
    for name in ('omit_row', 'scalar_type', 'unsafe_guard', 'fabricate_fresh', 'omit_cancel', 'cleanup', 'source', 'authority'):
        mutant = copy.deepcopy(raw)
        if name == 'omit_row':
            mutant['rows'].pop()
        elif name == 'scalar_type':
            mutant['rows'][0]['timed']['accepted'] = 1
        elif name == 'unsafe_guard':
            row = next(r for r in mutant['rows'] if r['policy'] == 'shield_deadline' and r['schedule'] == 'decision_delay')
            row['timed']['accepted'] = True
        elif name == 'fabricate_fresh':
            row = next(r for r in mutant['rows'] if r['policy'] == 'direct' and r['schedule'] == 'timeout' and r['suppress_cancel'])
            row['timed']['decision_ns'] = row['deadline_ns'] - 1
        elif name == 'omit_cancel':
            row = next(r for r in mutant['rows'] if r['policy'] == 'direct' and r['schedule'] == 'timeout')
            row['events'] = [e for e in row['events'] if e['name'] != 'producer_cancel']
        elif name == 'cleanup':
            mutant['rows'][0]['all_tasks_terminal'] = False
        elif name == 'source':
            mutant['source_sha256'] = '0' * 64
        else:
            mutant['input_dispatched'] = True
        bad = verify(mutant)
        controls.append({'control': name, 'rejected': bool(bad), 'errors': bad})
    summary = {}
    for policy in ('direct', 'shield', 'shield_deadline'):
        rows = [r for r in raw['rows'] if r['policy'] == policy]
        summary[policy] = {'rows': len(rows), 'late_admissions': sum(r['timed']['accepted'] and r['timed']['decision_ns'] >= r['deadline_ns'] for r in rows),
                           'companion_cancelled': sum(r['companion']['terminal'] == 'cancelled' for r in rows)}
    output = {'status': 'PASS_WAITER_DEADLINE_CONSTRUCTION_SCOPED' if not errors and all(c['rejected'] for c in controls) else 'FAIL_AUDIT',
              'rows': len(raw['rows']), 'waiter_outcomes': 2 * len(raw['rows']), 'errors': errors,
              'summary': summary, 'corruption_controls': controls, 'independent_implementation_same_author': True,
              'raw_sha256': hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest()}
    with Path(sys.argv[2]).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(output, stream, sort_keys=True, indent=2)
        stream.write('\n')
    print(json.dumps(output))
    raise SystemExit(0 if output['status'].startswith('PASS') else 1)
