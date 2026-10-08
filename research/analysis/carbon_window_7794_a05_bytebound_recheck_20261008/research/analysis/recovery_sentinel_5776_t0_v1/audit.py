#!/usr/bin/env python3
"""Independent ledger auditor; does not import candidate runner."""
import json
from pathlib import Path

fx = json.loads(Path('/work/fixtures.json').read_text())
raw = json.loads(Path('/work/raw.json').read_text())
assert raw['schema'] == 'recovery-sentinel-raw-v1'
assert raw['fixture_sha256'] == __import__('hashlib').sha256(Path('/work/fixtures.json').read_bytes()).hexdigest()
expected = len(fx['loads']) * len(fx['mechanisms']) * fx['episodes_per_load']
assert len(raw['episodes']) == expected
ids = [e['episode_id'] for e in raw['episodes']]
assert len(set(ids)) == expected, 'duplicate or missing prospective episode IDs'
checks = 0
errors = []
for e in raw['episodes']:
    ev = e['events']
    assert len(ev) == fx['horizon_ticks']
    assert [x['tick'] for x in ev] == list(range(fx['horizon_ticks']))
    prev = 0
    observed_returns = []
    pending = None
    for x in ev:
        expected_backlog = max(0, prev + x['demand'] + x['injected_delay'] - x['service'])
        if x['backlog'] != expected_backlog:
            errors.append([e['episode_id'], x['tick'], 'backlog'])
        if x['in_envelope'] != (x['backlog'] <= fx['return_envelope_backlog_max']):
            errors.append([e['episode_id'], x['tick'], 'envelope'])
        prev = x['backlog']; checks += 1
        if x['disturbance']:
            pending = {'probe': len(observed_returns)+1, 'start': x['tick'], 'delay': x['injected_delay']}
        elif pending is not None and x['in_envelope']:
            observed_returns.append({'probe': pending['probe'], 'start': pending['start'],
                                     'tick': x['tick'], 'recovery_ticks': x['tick']-pending['start'],
                                     'delay': pending['delay']})
            pending = None
    if observed_returns != e['returns']:
        errors.append([e['episode_id'], 'returns'])
    # Verify fixed waveform outside the explicitly variable-disturbance negative control.
    expected_ticks = fx['disturbance']['start_ticks']
    actual = [x for x in ev if x['disturbance']]
    if [x['tick'] for x in actual] != expected_ticks:
        errors.append([e['episode_id'], 'probe_schedule'])
    if e['mechanism'] != 'variable_disturbance' and any(x['injected_delay'] != fx['disturbance']['delay_ticks'] for x in actual):
        errors.append([e['episode_id'], 'probe_magnitude'])

recomputed = [
  [e['episode_id'], len(e['returns']), e['slowdown_ratio'], e['warning']]
  for e in raw['episodes']
]
for e, (_, nret, ratio, warning) in zip(raw['episodes'], recomputed):
    returns = e['returns']
    calc = returns[-1]['recovery_ticks'] / returns[0]['recovery_ticks'] if len(returns) >= 2 and returns[0]['recovery_ticks'] else 1.0
    if calc != ratio or (calc >= fx['warning']['threshold_slowdown_ratio']) != warning:
        errors.append([e['episode_id'], 'statistic'])

assert not errors, json.dumps(errors[:10])
counts = {}
for e in raw['episodes']:
    k = (e['load'], e['mechanism'])
    q = counts.setdefault(k, {'episodes':0, 'warnings':0, 'losses':0})
    q['episodes'] += 1; q['warnings'] += int(e['warning']); q['losses'] += int(bool(e['loss_ticks']))
print(json.dumps({'audit':'PASS_LEDGER_SCOPED','episodes':expected,'event_rows_checked':checks,'errors':0,'groups':{f'{k[0]}:{k[1]}':v for k,v in sorted(counts.items())}},sort_keys=True,separators=(',',':')))

