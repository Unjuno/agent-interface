"""Bounded passive sampling before a planner boundary, without input authority.

Equality describes two received full frames and sampled X context only. It is
not application readiness, semantic effect verification, or a future guarantee.
Use validated observations from one durable session; capture() must return a
completed observation-only result's image/observation and correlated clock.
"""
from PIL import Image
import hashlib


def compare(previous, fresh):
    old, new, clock = previous['observation'], fresh['observation'], fresh['clock']
    base = {'matched': False, 'authority': 'none'}
    if (new['sequence'] <= old['sequence'] or new['capture_ns'] <= old['capture_ns'] or
            clock['sequence'] != new['sequence'] or
            not 0 <= clock['runtime_ns'] - new['capture_ns'] < 1_000_000_000):
        return dict(base, reason='invalid_sequence_or_time')
    for observation in (old, new):
        binding = observation.get('pointer_binding') or {}
        if not binding.get('focus') or not binding.get('surface') or not binding.get('geometry'):
            return dict(base, reason='missing_context')
        for side in ('before', 'after'):
            state = observation.get('input_state_' + side) or {}
            if (observation.get('input_focus_' + side) != binding['focus'] or
                    observation.get('pointer_context_' + side) != binding or
                    state.get('focus') != binding['focus'] or
                    state.get('owned_buttons') != [] or state.get('owned_keycodes') != []):
                return dict(base, reason='incoherent_or_owned_input_sample')
    if old['pointer_binding'] != new['pointer_binding']:
        return dict(base, reason='context_changed')
    with Image.open(previous['image']) as a, Image.open(fresh['image']) as b:
        if (a.mode, a.size) != (b.mode, b.size):
            return dict(base, reason='image_layout_changed')
        before, after = a.tobytes(), b.tobytes()
    matched = before == after
    return dict(base, matched=matched, reason='received_pair_equal' if matched else 'pixels_changed',
                source_pixels_sha256=hashlib.sha256(before).hexdigest(),
                fresh_pixels_sha256=hashlib.sha256(after).hexdigest())


def collect(initial, capture, max_samples=3):
    if type(max_samples) is not int or not 1 <= max_samples <= 3:
        raise ValueError('max_samples must be1..3')
    previous = initial
    checks = []
    for _ in range(max_samples):
        fresh = capture()
        verdict = compare(previous, fresh)
        checks.append({'source': previous['observation'], 'fresh': fresh['observation'],
                       'clock': fresh['clock'], 'verdict': verdict})
        previous = fresh
        if verdict['matched']:
            break
    return {'status': 'received_pair_equal' if checks[-1]['verdict']['matched'] else 'sample_limit',
            'observation': previous['observation'], 'checks': checks, 'authority': 'none',
            'scope': 'bounded passive full-frame/context samples; semantic readiness and effects unknown'}
