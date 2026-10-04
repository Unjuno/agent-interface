"""Bounded sampled visual stability, not task readiness or input authority."""
from PIL import Image
from sampled_target_contract_v1 import evaluate


def collect(initial, capture, contract, max_samples=3):
    if type(max_samples) is not int or not 1 <= max_samples <= 4:
        raise ValueError('max_samples must be1..4')
    previous = initial
    checks = []
    for _ in range(max_samples):
        fresh = capture()
        with Image.open(previous['image']) as old, Image.open(fresh['image']) as new:
            verdict = evaluate(contract, {'intent': contract['name'], 'execute_once': True},
                               previous['observation'], fresh['observation'], old, new,
                               fresh['clock']['runtime_ns'])
        checks.append({'source': previous['observation'], 'fresh': fresh['observation'],
                       'clock': fresh['clock'], 'verdict': verdict})
        if verdict['eligible']:
            return {'stable': True, 'checks': checks, 'authority': 'none',
                    'scope': 'two matching received samples only; semantic readiness unknown'}
        if verdict['reason'] != 'target_patch_changed':
            break
        previous = fresh
    return {'stable': False, 'checks': checks, 'authority': 'none',
            'scope': 'bounded observations exhausted or invalid context; no automatic model/input continuation'}
