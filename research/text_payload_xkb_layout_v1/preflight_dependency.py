"""Experimental whole-payload lowering for first-group, two-level ASCII only.

No clipboard, keymap writes, network, or universal input.text support claim.
Preflight rejection is zero-input; interruption after commit is NOT rollback.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
import time


class Rejected(ValueError):
    pass


@dataclass(frozen=True)
class Plan:
    text: str
    strokes: tuple[tuple[int, bool], ...]
    shift_code: int
    map_hash: str


def fingerprint(mapping: list[list[int]]) -> str:
    return hashlib.sha256(json.dumps(mapping, separators=(',', ':')).encode()).hexdigest()


def prepare(text: str, mapping: list[list[int]], first_code: int = 8) -> Plan:
    if type(text) is not str or len(text) > 16384:
        raise Rejected('INVALID_TEXT')
    if type(first_code) is not int or not 8 <= first_code <= 255:
        raise Rejected('INVALID_KEYMAP')
    if type(mapping) is not list or not mapping or len(mapping) + first_code > 256:
        raise Rejected('INVALID_KEYMAP')
    symbols: dict[int, tuple[int, bool]] = {}
    shift_code = 0
    for offset, levels in enumerate(mapping):
        if not isinstance(levels, list) or len(levels) < 2 or any(type(x) is not int or x < 0 for x in levels):
            raise Rejected('INVALID_KEYMAP')
        code = first_code + offset
        if levels[0] == 0xFFE1:  # Shift_L at unshifted first-group level.
            shift_code = code
        for level in (0, 1):
            symbol = levels[level]
            candidate = (code, level == 1)
            if 32 <= symbol <= 126:
                old = symbols.get(symbol)
                if old is None or (candidate[1], candidate[0]) < (old[1], old[0]):
                    symbols[symbol] = candidate
    strokes = []
    for char in text:
        if not 32 <= ord(char) <= 126:
            raise Rejected('TEXT_OUTSIDE_PRINTABLE_ASCII')
        stroke = symbols.get(ord(char))
        if stroke is None or (stroke[1] and not shift_code):
            raise Rejected('TEXT_NOT_REPRESENTABLE_IN_KEYMAP')
        strokes.append(stroke)
    return Plan(text, tuple(strokes), shift_code, fingerprint(mapping))


def keyboard_mapping(d) -> list[list[int]]:
    info = d.display.info
    return [list(row) for row in d.get_keyboard_mapping(info.min_keycode, info.max_keycode-info.min_keycode+1)]


def physical_state(d) -> dict:
    bits = d.query_keymap()
    return {'keys': [k for k in range(8, 256) if bits[k//8] & (1 << (k%8))],
            'mask': int(d.screen().root.query_pointer().mask)}


def deliver(backend, text: str, *, target: int, observation: int, current_observation: int,
            revision: int, current_revision: int, expires_ns: int, pacing_s: float = .012) -> dict:
    """Commit one preflighted text op. Caller must acquire/focus target separately."""
    from Xlib import X
    from Xlib.ext import xtest
    start = backend.emissions
    receipt = {'accepted': False, 'error': None, 'emissions': 0,
               'preflight_rejected': True, 'interrupted': False}
    owned: set[int] = set()
    def send(code, down):
        # Track before sync so a sync error still attempts cleanup.
        if down:
            owned.add(code)
        xtest.fake_input(backend.d, X.KeyPress if down else X.KeyRelease, code)
        backend.emissions += 1
        backend.d.sync()
        if not down:
            owned.discard(code)
    try:
        integers = (target, observation, current_observation, revision, current_revision, expires_ns)
        if any(type(x) is not int or x < 0 for x in integers) or target == 0:
            raise Rejected('INVALID_CONTEXT')
        if not isinstance(pacing_s, (int, float)) or isinstance(pacing_s, bool) or not 0 <= pacing_s <= .1:
            raise Rejected('INVALID_PACING')
        if time.monotonic_ns() >= expires_ns:
            raise Rejected('LEASE_EXPIRED')
        if observation != current_observation:
            raise Rejected('STALE_OBSERVATION')
        if revision != current_revision:
            raise Rejected('STALE_BINDING')
        mapping = keyboard_mapping(backend.d)
        plan = prepare(text, mapping, backend.d.display.info.min_keycode)
        state = physical_state(backend.d)
        if state['keys'] or state['mask']:
            raise Rejected('NON_NEUTRAL_INPUT')
        if getattr(backend.d.get_input_focus().focus, 'id', None) != target:
            raise Rejected('FOCUS_MISMATCH')
        # Read-only recheck. This is not an atomic X server transaction.
        if fingerprint(keyboard_mapping(backend.d)) != plan.map_hash:
            raise Rejected('KEYMAP_CHANGED')
        if time.monotonic_ns() >= expires_ns:
            raise Rejected('LEASE_EXPIRED')
        receipt.update(accepted=True, preflight_rejected=False, map_hash=plan.map_hash)
        for code, shift in plan.strokes:
            if time.monotonic_ns() >= expires_ns:
                raise Rejected('LEASE_EXPIRED_DURING_EXECUTION')
            if getattr(backend.d.get_input_focus().focus, 'id', None) != target:
                raise Rejected('FOCUS_CHANGED_DURING_EXECUTION')
            if shift:
                send(plan.shift_code, True)
            send(code, True)
            send(code, False)
            if shift:
                send(plan.shift_code, False)
            time.sleep(pacing_s)
    except Rejected as exc:
        receipt['error'] = str(exc)
        receipt['interrupted'] = receipt['accepted']
    finally:
        for code in sorted(owned):
            send(code, False)
        receipt['emissions'] = backend.emissions-start
        state = physical_state(backend.d)
        receipt['physical_after'] = state
        receipt['release_verified'] = not state['keys'] and not state['mask']
    return receipt
