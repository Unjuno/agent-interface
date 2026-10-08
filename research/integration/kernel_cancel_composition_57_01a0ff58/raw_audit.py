"""Separate finite contract oracle; imports no producer or tested kernel."""
import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAMES = ['prestart_none', 'prestart_observed', 'equalstart_none', 'later_possible',
         'cancel_before', 'cancel_equal', 'cancel_later', 'no_begin', 'expired_begin',
         'duplicate_earlier', 'duplicate_later', 'stale_then_fresh']


def expected(arm, name):
    release_guard, cancel_guard, uncertainty = (bit == '1' for bit in arm)
    events = []
    def event(op, accepted):
        events.append({'op': op, 'accepted': accepted, 'exception': None if accepted else 'ContractError'})
    begun = name not in ('no_begin', 'expired_begin')
    if name != 'no_begin':
        event('begin:300' if begun else 'begin:1000', begun)
    if name in ('duplicate_earlier', 'duplicate_later'):
        event('begin:200' if name == 'duplicate_earlier' else 'begin:800', False)
    execution = name in ('prestart_none', 'prestart_observed', 'equalstart_none', 'later_possible')
    if execution:
        time = 399 if name in ('prestart_none', 'prestart_observed') else (400 if name == 'equalstart_none' else 600)
        execution = not (release_guard and time < 400)
        event('construct_execution:' + str(time), execution)
        if execution:
            event('record_execution', True)
    time = {'cancel_before': 299, 'cancel_equal': 300, 'duplicate_earlier': 250,
            'duplicate_later': 400, 'no_begin': 300, 'stale_then_fresh': 299}.get(name, 600)
    stopped = not (cancel_guard and begun and not execution and time < 300)
    event('stop:' + str(time), stopped)
    if name == 'stale_then_fresh' and not stopped:
        event('stop:600', True)
        stopped = True
    outcome = None
    if stopped:
        possible = (name in ('prestart_observed', 'later_possible')) if execution else begun and uncertainty
        outcome = {'stage': 'stopped', 'reason': 'cancelled', 'command_id': 'c' if begun else None,
                   'effect_occurred': possible, 'effect_verified': False, 'release_verified': True}
    return {'case': name, 'events': events, 'stage': 'stopped' if stopped else 'authorized', 'outcome': outcome}


def signature(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def audit(raw):
    errors = []
    freeze = json.loads((HERE / 'FREEZE.json').read_bytes())
    if raw.get('study') != freeze['study'] or raw.get('freeze_sha256') != hashlib.sha256((HERE / 'FREEZE.json').read_bytes()).hexdigest():
        errors.append('identity')
    required = [''.join(bits) for bits in itertools.product('01', repeat=3)]
    if type(raw.get('arms')) is not list or [a.get('arm') for a in raw['arms']] != required:
        errors.append('arm census')
        return errors
    for actual in raw['arms']:
        arm = actual['arm']
        if signature(actual.get('source_sha256')) != signature(freeze['arms'][arm]):
            errors.append('source:' + arm)
        wanted = [expected(arm, name) for name in NAMES]
        if signature(actual.get('rows')) != signature(wanted):
            errors.append('typed rows:' + arm)
    return errors


if __name__ == '__main__':
    raw = json.loads((HERE / 'run-01/raw.json').read_bytes())
    errors = audit(raw)
    result = {'status': 'PASS_COMPOSITION_SCOPED' if not errors else 'HOLD',
              'errors': errors, 'rows': sum(len(a['rows']) for a in raw['arms']),
              'scope': '96 sequential typed synthetic histories; no live or full-tree merge claim'}
    with (HERE / 'run-01/audit.json').open('x', encoding='utf-8', newline='\n') as handle:
        handle.write(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps(result))
    raise SystemExit(bool(errors))
