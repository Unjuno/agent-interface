"""Separate JSON-only literal oracle; no matrix/kernel imports or invocation."""
import copy
import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def same(a, b):
    return json.dumps(a, sort_keys=True, separators=(',', ':'), allow_nan=False) == json.dumps(
        b, sort_keys=True, separators=(',', ':'), allow_nan=False)


def check(data, fixture, freeze):
    if type(data) is not dict or set(data) != {'schema', 'id', 'source_sha256', 'rows'}:
        raise ValueError('document schema')
    if data['schema'] != 'kernel-effect-start-ordinary-v1' or data['id'] != freeze['id']:
        raise ValueError('identity')
    if not same(data['source_sha256'], freeze['source_sha256']): raise ValueError('source identity')
    expected = list(itertools.product(('baseline', 'candidate'), fixture['statuses'],
                                     fixture['effect_times_ns'], fixture['identities']))
    if type(data['rows']) is not list or len(data['rows']) != len(expected): raise ValueError('census')
    counts = {arm: {'accepted': 0, 'stale_matching_accepted': 0, 'identity_refused': 0}
              for arm in ('baseline', 'candidate')}
    for row, (arm, status, ns, identity) in zip(data['rows'], expected):
        fields = {'arm', 'status', 'observed_ns', 'identity', 'attempt', 'before', 'accepted',
                  'error', 'after', 'outcome'}
        if type(row) is not dict or set(row) != fields: raise ValueError('row schema')
        if not same([row['arm'], row['status'], row['observed_ns'], row['identity']],
                    [arm, status, ns, identity]): raise ValueError('row join')
        if type(row['accepted']) is not bool: raise ValueError('accepted must be boolean')
        attempt = {'command_id': 'other' if identity == 'wrong_command' else 'command',
                   'invariant_manifest_id': 'a' * 64 if identity == 'wrong_manifest' else 'b' * 64,
                   'observed_ns': ns, 'status': status, 'evidence_digest': 'd' * 64}
        if not same(row['attempt'], attempt) or not same(row['before'], fixture['before']):
            raise ValueError('input/full pre-state')
        wanted = identity == 'matching' and (arm == 'baseline' or ns >= 600)
        if row['accepted'] is not wanted: raise ValueError('admission predicate')
        after = copy.deepcopy(fixture['before'])
        if wanted:
            after['effect'] = attempt
            after['stage'] = status
            outcome = {'stage': status, 'reason': status, 'command_id': 'command',
                       'effect_occurred': True, 'effect_verified': status == 'verified',
                       'release_verified': True}
            if row['error'] is not None or not same(row['outcome'], outcome): raise ValueError('terminal evidence')
            counts[arm]['accepted'] += 1
            counts[arm]['stale_matching_accepted'] += int(ns < 600)
        else:
            if type(row['error']) is not str or not row['error'] or row['outcome'] is not None:
                raise ValueError('refusal evidence')
            counts[arm]['identity_refused'] += int(identity != 'matching')
        if not same(row['after'], after): raise ValueError('full post-state custody')
    if counts != {'baseline': {'accepted': 30, 'stale_matching_accepted': 12, 'identity_refused': 60},
                  'candidate': {'accepted': 18, 'stale_matching_accepted': 0, 'identity_refused': 60}}:
        raise ValueError('prospective totals')
    return counts


def main():
    output = HERE / 'audit.json'
    if output.exists(): raise FileExistsError('primary raw audit already retained')
    freeze = json.loads((HERE / 'MATRIX_FREEZE.json').read_bytes())
    for name, expected in freeze['inputs_sha256'].items():
        if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != expected:
            raise ValueError(('input pin', name))
    fixture = json.loads((HERE / 'fixture.json').read_bytes())
    original = json.loads((HERE / 'raw.json').read_bytes())
    counts = check(original, fixture, freeze)
    controls = []
    for name, mutate in (
        ('boolean_alias', lambda d: d['rows'][0].update(observed_ns=False)),
        ('float_alias', lambda d: d['rows'][0].update(observed_ns=0.0)),
        ('changed_admission', lambda d: d['rows'][0].update(accepted=False)),
        ('refusal_loses_execution', lambda d: d['rows'][1]['after'].update(execution=None)),
        ('changed_effect_truth', lambda d: d['rows'][0]['outcome'].update(effect_verified=False)),
        ('missing_row', lambda d: d['rows'].pop()),
        ('wrong_source', lambda d: d['source_sha256']['baseline'].update(lifecycle='0' * 64)),
        ('extra_state', lambda d: d['rows'][0]['before'].update(extra=None)),
    ):
        changed = copy.deepcopy(original)
        mutate(changed)
        if same(changed, original): raise ValueError(('ineffective control', name))
        try: check(changed, fixture, freeze)
        except ValueError as e: controls.append({'name': name, 'refused': True, 'reason': str(e)})
        else: raise ValueError(('control accepted', name))
    result = {'id': freeze['id'], 'decision': 'PASS_TYPED_RECORDED_START_CONSTRUCTION',
              'rows': len(original['rows']), 'counts': counts, 'controls': controls,
              'raw_sha256': hashlib.sha256((HERE / 'raw.json').read_bytes()).hexdigest(),
              'scope': 'Exact two source snapshots, sequential typed comparable-clock fixture only; no physical/task/public-path/performance/provenance claim.'}
    with output.open('x', encoding='utf8', newline='\n') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(json.dumps(result))


if __name__ == '__main__': main()
