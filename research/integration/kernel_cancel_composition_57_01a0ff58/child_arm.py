"""Execute one exact source subset; no expected-result computation."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
arm = sys.argv[1]
sys.path.insert(0, str(ROOT / 'sources' / arm))
from runtime.kernel.contracts import (Action, ActionKind, AuthorityLease, ContractError,
    EffectOccurrence, ExecutionReceipt, ExecutionRequest, Observation, ReleaseReceipt, TargetBinding)
from runtime.kernel.lifecycle import RequestLifecycle

CASES = (
    'prestart_none', 'prestart_observed', 'equalstart_none', 'later_possible',
    'cancel_before', 'cancel_equal', 'cancel_later', 'no_begin', 'expired_begin',
    'duplicate_earlier', 'duplicate_later', 'stale_then_fresh')


def run_case(name):
    life = RequestLifecycle()
    events = []
    observation = Observation(1, 100, 's', 'a' * 64, 10, 10, 'raw')
    binding = TargetBinding('t', 1, 's', 'b' * 64)
    lease = AuthorityLease('l', 1, 's', 1000, frozenset({ActionKind.KEY}))
    request = ExecutionRequest('c', 'd' * 64, binding, lease,
                               (Action('a', ActionKind.KEY, 'pulse'),))
    life.record_observation(observation)
    life.bind(binding)
    life.authorize(lease, now_ns=200)

    def call(label, fn):
        try:
            value = fn()
        except ContractError:
            events.append({'op': label, 'accepted': False, 'exception': 'ContractError'})
            return False, None
        events.append({'op': label, 'accepted': True, 'exception': None})
        return True, value

    if name != 'no_begin':
        call('begin:1000' if name == 'expired_begin' else 'begin:300',
             lambda: life.begin_execution(request, now_ns=1000 if name == 'expired_begin' else 300))
    if name.startswith('duplicate_'):
        duplicate = 200 if name == 'duplicate_earlier' else 800
        call('begin:' + str(duplicate), lambda: life.begin_execution(request, now_ns=duplicate))
    if name in ('prestart_none', 'prestart_observed', 'equalstart_none', 'later_possible'):
        release_time = 399 if name.startswith('prestart') else 400 if name == 'equalstart_none' else 600
        occurrence = EffectOccurrence.OBSERVED if name == 'prestart_observed' else (
                     EffectOccurrence.POSSIBLE if name == 'later_possible' else EffectOccurrence.NONE)
        okay, receipt = call('construct_execution:' + str(release_time), lambda: ExecutionReceipt(
            'c', 'r', 'd' * 64, 'l', 1, 's', 400, 500, 1, occurrence,
            ReleaseReceipt(release_time, True)))
        if okay:
            call('record_execution', lambda: life.record_execution(receipt))
    cancel_time = {'cancel_before': 299, 'cancel_equal': 300, 'duplicate_earlier': 250,
                   'duplicate_later': 400, 'no_begin': 300, 'stale_then_fresh': 299}.get(name, 600)
    okay, _ = call('stop:' + str(cancel_time), lambda: life.stop('cancelled', release=ReleaseReceipt(cancel_time, True)))
    if name == 'stale_then_fresh' and not okay:
        call('stop:600', lambda: life.stop('cancelled', release=ReleaseReceipt(600, True)))
    outcome = None
    if life.stage.value == 'stopped':
        value = life.outcome()
        outcome = {'stage': value.stage.value, 'reason': value.reason,
                   'command_id': value.command_id, 'effect_occurred': value.effect_occurred,
                   'effect_verified': value.effect_verified, 'release_verified': value.release_verified}
    return {'case': name, 'events': events, 'stage': life.stage.value, 'outcome': outcome}


print(json.dumps({'arm': arm, 'rows': [run_case(name) for name in CASES]}, sort_keys=True))
