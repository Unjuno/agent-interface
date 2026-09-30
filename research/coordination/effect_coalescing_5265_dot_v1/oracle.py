"""Independent application-effect cardinality scorer.
Uses fixture-authored goal labels and denial facts, never semantic keys/model code.
"""
from collections import Counter

def score(case, outcome):
    expected_events=[e for e in case['events'] if e['kind']!='transition']
    if len(outcome['decisions']) != len(expected_events):
        return dict(integrity_errors=['decision_count'],duplicates=0,missing=0,unauthorized=0,cross_goal_merges=0)
    wanted={e['oracle_goal'] for e in expected_events if e['oracle_goal'] is not None}
    actual=Counter()
    illegal=merges=0
    errors=[]
    for index,(e,row) in enumerate(zip(expected_events,outcome['decisions'])):
        goal=e['oracle_goal']
        if row['effect'] not in (0,1): errors.append('effect_not_bit')
        if row['effect']:
            if goal is None: illegal+=1
            else: actual[goal]+=1
            if row['status']!='EXECUTED': errors.append('effect_without_executed')
        if e.get('oracle_deny') and row['status']!=e['oracle_deny']:
            errors.append(f'denial_mismatch:{index}')
        to=row.get('coalesced_to')
        if to is not None:
            if type(to) is not int or not 0<=to<index:
                errors.append('invalid_merge_reference')
            elif goal is None or expected_events[to]['oracle_goal']!=goal:
                merges+=1
        if row.get('held') is not False: errors.append('held_input')
    if outcome.get('neutral') is not True: errors.append('terminal_not_neutral')
    if outcome.get('authority_created')!=0: errors.append('authority_created')
    return dict(integrity_errors=errors,duplicates=sum(max(0,n-1) for n in actual.values()),missing=len(wanted-set(actual)),unauthorized=illegal,cross_goal_merges=merges)
