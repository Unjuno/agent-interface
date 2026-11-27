"""Existing two-target native form method, without model calls or automatic repair.

Target eligibility and verified release remain owned by NativeHandleBridge.
Completion here is program completion; it does not verify entered text or save.
"""
import math
import time


def fill_and_submit(bridge, handles, token, *, wait_ms, on_step):
    """Run the existing enter/submit pair; persist each result before proceeding.

    on_step(name, result) must retain the receipt. If it raises, no later step
    runs. A dispatch exception propagates because delivery can be uncertain.
    Each bridge.click revalidates its own target against fresh observations.
    """
    if type(handles) is not dict or set(handles) != {'field', 'submit'}:
        raise ValueError('explicit field and submit references required')
    for reference in handles.values():
        if (not isinstance(reference, (list, tuple)) or len(reference) != 2
                or type(reference[0]) is not str or not reference[0]
                or not isinstance(reference[1], (list, tuple)) or len(reference[1]) != 2
                or any(type(v) not in (int, float) or not math.isfinite(v) for v in reference[1])):
            raise ValueError('target alias and finite offset pair required')
    if type(token) is not str or type(wait_ms) is not int or not 0 <= wait_ms <= 1000:
        raise ValueError('text token and explicit wait_ms in 0..1000 required')
    if not callable(on_step):
        raise ValueError('receipt persistence callback required')
    started = time.monotonic_ns()
    results = {}
    completed = 0
    for name, target, tail in (
            ('entered', 'field', [{'op': 'key_chord', 'keys': ['CTRL', 'A']},
                                  {'op': 'text', 'text': token},
                                  {'op': 'wait_update', 'timeout_ms': wait_ms}]),
            ('saved', 'submit', [{'op': 'wait_update', 'timeout_ms': wait_ms}])):
        result = bridge.click(*handles[target], tail=tail)
        results[name] = result
        on_step(name, result)
        # Do not treat a successful-looking status as release verification.
        execution = result.get('execution', {})
        releases = execution.get('releases', [])
        released = bool(releases) and all(r.get('verified') is True
            and r.get('keys_down') == [] and r.get('buttons_down') == [] for r in releases)
        if result.get('status') != 'completed' or result.get('recovery_required') is not False or not released:
            return {'status': 'safe_yield', 'stopped_at': name,
                    'reason': 'execution_incomplete_or_release_unverified',
                    'completed_actions': completed, 'results': results,
                    'started_ns': started, 'ended_ns': time.monotonic_ns(),
                    'task_success': None, 'replay_allowed': False}
        completed += 1
    return {'status': 'completed', 'completed_actions': completed, 'results': results,
            'started_ns': started, 'ended_ns': time.monotonic_ns(),
            'task_success': None, 'replay_allowed': False}
