"""Separate list-based reference, exact raw reconstruction and corruptions.

Does not import the candidate and does not execute a producer.
"""
import copy
import hashlib
import itertools
import json
import sys

def reference(arrivals, mode, lag, schedule, policy):
    waiting = []
    history = []
    frames = []
    total = 0
    finishes = 0
    for time in range(8):
        history.append(len(waiting))
        measurement = 0 if mode == 'zero' else 2 if mode == 'high' else history[max(0, time-lag)]
        decisions = []
        new = 0
        for index in range(arrivals[time] if time < 5 else 0):
            name = '%d:%d' % (time, index)
            predicates = {
                'report_only': measurement + new < 2,
                'report_cap': measurement + new < 2 and len(waiting) < 2,
                'cap_only': len(waiting) < 2,
                'rate_cap': len(waiting) < 2 and new == 0,
            }
            accepted = predicates[policy]
            decisions.append([name, 'ADMIT' if accepted else 'UNKNOWN'])
            if accepted:
                waiting = waiting + [name]
                new += 1
                total += 1
        highwater = len(waiting)
        available = {'unit': True, 'alternate': time % 2 == 0, 'stall': time >= 3}[schedule] or time >= 5
        result = waiting[0] if waiting and available else None
        if result is not None:
            waiting = waiting[1:]
            finishes += 1
        frames.append(dict(tick=time, report=measurement, actions=decisions,
                           occupancy=highwater, completed=result, pending=waiting[:],
                           safety='safety:%d' % time))
    return dict(trace=frames, admitted=total, unknown=sum(arrivals)-total,
                verified=finishes, peak=max(f['occupancy'] for f in frames),
                pending=waiting[:], safety_serviced=8)

def check_row(row):
    if set(row) != {'arrivals', 'mode', 'delay', 'service', 'arms'}:
        raise ValueError('row schema')
    if set(row['arms']) != {'report_only', 'report_cap', 'cap_only', 'rate_cap'}:
        raise ValueError('arm set')
    for arm, observed in row['arms'].items():
        expected = reference(row['arrivals'], row['mode'], row['delay'], row['service'], arm)
        if observed != expected:
            raise ValueError('reference mismatch: ' + arm)

def audit(path):
    rows = 0
    counts = {a: dict(overflow_cases=0, admitted=0, unknown=0, verified=0, max_peak=0,
                      pending_cases=0) for a in ('report_only','report_cap','cap_only','rate_cap')}
    comparisons = {'cap_less_than_report_cap': 0, 'cap_more_than_report_cap': 0,
                   'cap_less_than_rate_cap': 0, 'cap_more_than_rate_cap': 0}
    witnesses = {}
    mutation_row = None
    digest = hashlib.sha256()
    with open(path, 'rb') as raw:
        specifications = itertools.product(itertools.product(range(3), repeat=5),
                                            ('honest','zero','high'), range(3),
                                            ('unit','alternate','stall'))
        for arrivals, mode, lag, service in specifications:
            line = raw.readline()
            if not line:
                raise ValueError('missing row')
            digest.update(line)
            row = json.loads(line)
            if (row['arrivals'], row['mode'], row['delay'], row['service']) != (list(arrivals),mode,lag,service):
                raise ValueError('fixture ordering/identity')
            check_row(row)
            rows += 1
            for arm, value in row['arms'].items():
                stat = counts[arm]
                stat['overflow_cases'] += value['peak'] > 2
                stat['pending_cases'] += bool(value['pending'])
                stat['max_peak'] = max(stat['max_peak'], value['peak'])
                for field in ('admitted','unknown','verified'):
                    stat[field] += value[field]
                if value['peak'] > 2 and 'overflow' not in witnesses:
                    witnesses['overflow'] = row
            baseline = row['arms']['cap_only']['verified']
            for other in ('report_cap','rate_cap'):
                other_value = row['arms'][other]['verified']
                comparisons['cap_less_than_'+other] += baseline < other_value
                comparisons['cap_more_than_'+other] += baseline > other_value
                if baseline > other_value and other not in witnesses:
                    witnesses[other] = row
            if mutation_row is None and sum(arrivals) > 0:
                mutation_row = row
        if raw.read(1):
            raise ValueError('extra rows')
    corruptions = []
    for name in ('missing_offer','forged_verified','hidden_overflow','lost_safety','wrong_report','cross_task_completion'):
        changed = copy.deepcopy(mutation_row)
        target = changed['arms']['cap_only']
        if name == 'missing_offer':
            next(f for f in target['trace'] if f['actions'])['actions'].pop()
        elif name == 'forged_verified':
            target['verified'] += 1
        elif name == 'hidden_overflow':
            target['peak'] = 0
        elif name == 'lost_safety':
            target['trace'][0]['safety'] = None
        elif name == 'wrong_report':
            target['trace'][0]['report'] += 1
        else:
            next(f for f in target['trace'] if f['completed'] is not None)['completed'] = 'foreign:0'
        if changed == mutation_row:
            raise ValueError('ineffective corruption')
        try:
            check_row(changed)
        except ValueError:
            corruptions.append(name)
        else:
            raise ValueError('corruption accepted: ' + name)
    decision = ('SUBSUMED_BY_AUTHORITATIVE_CAP_SCOPED' if
                counts['report_only']['overflow_cases'] > 0 and
                all(counts[a]['overflow_cases'] == 0 and counts[a]['pending_cases'] == 0
                    for a in ('report_cap','cap_only','rate_cap')) and
                comparisons['cap_less_than_report_cap'] == 0 and
                comparisons['cap_more_than_report_cap'] > 0 and
                comparisons['cap_less_than_rate_cap'] == 0
                else 'FAIL_DECLARED_FINITE_HYPOTHESIS')
    return dict(decision=decision, audit='PASS_EXACT_FINITE_REFERENCE', rows=rows,
                raw_sha256=digest.hexdigest(), counts=counts, comparisons=comparisons,
                effective_corruptions_rejected=corruptions, witnesses=witnesses)

if __name__ == '__main__':
    result = audit(sys.argv[1])
    with open(sys.argv[2], 'x', encoding='utf-8', newline='\n') as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'witnesses'}, sort_keys=True))
