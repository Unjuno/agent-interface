"""Independent raw-only finite oracle. Does not import probe or kernel."""
import json
from pathlib import Path
import sys

STATES = ('new', 'observed', 'bound', 'authorized', 'begun', 'executed',
          'verified', 'contradicted', 'unavailable', 'stopped',
          'invalid_first_begin', 'duplicate_begin')
TIMES = (0, 199, 200, 299, 300, 301, 700, 800)
TERMINAL = {'verified', 'contradicted', 'unavailable', 'stopped'}
ACTIVE = {'authorized', 'begun', 'invalid_first_begin', 'duplicate_begin'}
BEGUN = {'begun', 'duplicate_begin'}


def before_for(state):
    stage = 'authorized' if state in ACTIVE else state
    command = 'command' if state in BEGUN | TERMINAL | {'executed'} else None
    effect = state if state in {'verified', 'contradicted', 'unavailable'} else None
    return {'stage': stage, 'command_id': command,
            'stop_reason': 'already_stopped' if state == 'stopped' else None,
            'effect_status': effect}


def audit(rows, mode):
    errors, seen, stale_accepts = [], set(), 0
    keys = {'mode','state','release_kind','release_ns','before','accepted',
            'after','error','release_verified'}
    if type(rows) is not list or len(rows) != 300:
        return {'decision': 'FAIL_AUDIT', 'errors': ['row_count'], 'rows': 0}
    for index, row in enumerate(rows):
        if type(row) is not dict or set(row) != keys:
            errors.append(f'{index}:shape'); continue
        state, kind, ns = row['state'], row['release_kind'], row['release_ns']
        if state not in STATES or kind not in ('missing','empty','unverified','held'):
            errors.append(f'{index}:identity'); continue
        if (kind == 'missing' and ns is not None) or (kind != 'missing' and (type(ns) is not int or ns not in TIMES)):
            errors.append(f'{index}:timestamp'); continue
        identity = (state, kind, ns)
        if identity in seen:
            errors.append(f'{index}:duplicate')
        seen.add(identity)
        expected = state not in TERMINAL
        if state in ACTIVE:
            expected = kind == 'empty'
        stale = state in BEGUN and kind == 'empty' and ns < 300
        if mode == 'candidate' and stale:
            expected = False
        before = before_for(state)
        after = dict(before)
        if expected:
            after.update(stage='stopped', stop_reason='cancelled')
        if row['mode'] != mode or type(row['accepted']) is not bool or row['accepted'] is not expected:
            errors.append(f'{index}:acceptance')
        if row['before'] != before or row['after'] != after:
            errors.append(f'{index}:state')
        if expected:
            if row['error'] is not None or row['release_verified'] is not True:
                errors.append(f'{index}:terminal_evidence')
        elif type(row['error']) is not str or not row['error'] or row['release_verified'] is not None:
            errors.append(f'{index}:refusal_evidence')
        if stale and row['accepted'] is True:
            stale_accepts += 1
    identities = {(s,k,n) for s in STATES for k in ('missing','empty','unverified','held')
                  for n in ((None,) if k == 'missing' else TIMES)}
    if seen != identities:
        errors.append('complete_denominator')
    if stale_accepts != (8 if mode == 'baseline' else 0):
        errors.append('stale_acceptance_count')
    return {'decision': 'FAIL_AUDIT' if errors else ('GAP_REPRODUCED_SCOPED' if mode == 'baseline' else 'PASS_CANDIDATE_SCOPED'),
            'rows': len(rows), 'stale_acceptances': stale_accepts, 'errors': errors}


if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] not in ('baseline','candidate'):
        raise SystemExit('usage: audit.py baseline|candidate raw.json')
    result = audit(json.loads(Path(sys.argv[2]).read_text()), sys.argv[1])
    print(json.dumps(result, indent=2))
    raise SystemExit(bool(result['errors']))
