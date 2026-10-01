#!/usr/bin/env python3
"""Synthetic recovery-sentinel candidate. Emits canonical JSON event ledger."""
import hashlib
import json
from pathlib import Path

FIXTURE = json.loads(Path('/work/fixtures.json').read_text())


def episode(load, mechanism, index):
    # Deterministic balanced synthetic population; index is a fixed episode ID.
    baseline_service = {'low': 5, 'near': 4, 'high': 3}[load]
    slowdown = {'low': 1, 'near': 1 + index % 2, 'high': 2 + index % 2}[load]
    if mechanism == 'abrupt_breaker':
        slowdown = 1
    if mechanism == 'no_collapse':
        slowdown = 1
    if mechanism == 'reset_hysteresis':
        slowdown = 1 if index % 2 == 0 else 2
    events = []
    backlog = 0
    service = baseline_service
    losses = []
    returns = []
    pending = None
    probe = 0
    for tick in range(FIXTURE['horizon_ticks']):
        demand = 1
        if mechanism == 'demand_drift' and tick >= 52:
            demand = 2
        disturbance = tick in FIXTURE['disturbance']['start_ticks']
        injected = FIXTURE['disturbance']['delay_ticks']
        if mechanism == 'variable_disturbance' and probe % 2:
            injected = 1
        if disturbance:
            probe += 1
        if mechanism == 'gradual_recovery' and disturbance and load == 'high':
            service += 1
        elif mechanism == 'gradual_recovery' and disturbance and load == 'near' and probe >= 3:
            service += 1
        elif mechanism == 'abrupt_breaker' and load == 'high' and tick >= 64:
            backlog = max(backlog, 9)
        elif mechanism == 'spontaneous_failure' and load == 'high' and tick == 67:
            backlog = max(backlog, 9)
        arrivals = demand + (injected if disturbance else 0)
        backlog = max(0, backlog + arrivals - service)
        if mechanism in ('abrupt_breaker', 'spontaneous_failure') and backlog >= FIXTURE['loss_of_service_backlog']:
            losses.append(tick)
        in_envelope = backlog <= FIXTURE['return_envelope_backlog_max']
        if disturbance:
            pending = {'probe': probe, 'start': tick, 'delay': injected}
        elif pending is not None and in_envelope:
            returns.append({'probe': pending['probe'], 'start': pending['start'],
                            'tick': tick, 'recovery_ticks': tick - pending['start'],
                            'delay': pending['delay']})
            pending = None
        events.append({'tick': tick, 'demand': demand, 'service': service,
                       'disturbance': disturbance, 'injected_delay': injected if disturbance else 0,
                       'backlog': backlog, 'in_envelope': in_envelope})
    # Candidate statistic: slope of successive fixed-probe recovery delays.
    observed = [r['recovery_ticks'] for r in returns]
    slowdown_ratio = (observed[-1] / observed[0]) if len(observed) >= 2 and observed[0] else 1.0
    warning = slowdown_ratio >= FIXTURE['warning']['threshold_slowdown_ratio']
    return {'episode_id': f'{load}-{mechanism}-{index:02d}', 'load': load,
            'mechanism': mechanism, 'events': events, 'returns': returns,
            'loss_ticks': losses, 'slowdown_ratio': slowdown_ratio,
            'warning': warning}


episodes = [episode(load, mechanism, i)
            for load in FIXTURE['loads']
            for mechanism in FIXTURE['mechanisms']
            for i in range(FIXTURE['episodes_per_load'])]
payload = {'schema': 'recovery-sentinel-raw-v1', 'fixture_sha256': hashlib.sha256(Path('/work/fixtures.json').read_bytes()).hexdigest(), 'episodes': episodes}
print(json.dumps(payload, sort_keys=True, separators=(',', ':')))

