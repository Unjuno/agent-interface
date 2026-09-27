"""Research-only strict resume receipt gate. No input, replay, or authority APIs.

The mapping API accepts JSON-native builtins owned by this call. Callers must not
mutate their mappings concurrently. Use decide_json for a private decoded copy.
This validates representation, NOT evidence authenticity, age, ancestry, or effects.
"""
from __future__ import annotations
import json
import re
from typing import Any

MAX_WIRE_BYTES = 16384
MAX_TOKEN_CHARS = 256
TOKEN = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,255}\Z', re.ASCII)
REQUIRED = frozenset(('session', 'frame_id', 'level', 'target_token', 'target_xid',
    'queue_version', 'source_generation', 'source_fresh', 'task_active',
    'pending_result', 'interrupt_resolved'))
OPTIONAL = frozenset(('value',))
TOKEN_FIELDS = ('session', 'frame_id', 'target_token')
BOOL_FIELDS = ('source_fresh', 'task_active', 'interrupt_resolved')
INT_BOUNDS = {'level': (0, 2147483647), 'target_xid': (1, 4294967295),
    'queue_version': (1, 18446744073709551615),
    'source_generation': (1, 18446744073709551615)}
PENDING = frozenset(('NONE', 'KNOWN', 'UNKNOWN'))


def _valid_receipt(value: object) -> bool:
    # Exact builtin types reject bool-as-int and custom truth/equality hooks.
    if type(value) is not dict:
        return False
    if any(type(k) is not str for k in value):
        return False
    keys = value.keys()
    if not REQUIRED.issubset(keys) or not keys <= (REQUIRED | OPTIONAL):
        return False
    for name in TOKEN_FIELDS:
        item = value[name]
        if type(item) is not str or TOKEN.fullmatch(item) is None:
            return False
    for name in BOOL_FIELDS:
        if type(value[name]) is not bool:
            return False
    for name, (lower, upper) in INT_BOUNDS.items():
        item = value[name]
        if type(item) is not int or not lower <= item <= upper:
            return False
    if type(value['pending_result']) is not str or value['pending_result'] not in PENDING:
        return False
    if 'value' in value and type(value['value']) is not str:
        return False
    return True


def _result(verdict: str, frame_id: str | None = None) -> dict[str, Any]:
    return {'verdict': verdict, 'eligible': verdict == 'RESUME',
            'input_authority': False, 'checked_frame_id': frame_id,
            'cached_success_reused': False}


def decide(saved: object, current: object) -> dict[str, Any]:
    """Fail closed on invalid representation; otherwise preserve ordered gates."""
    if not _valid_receipt(saved) or not _valid_receipt(current):
        return _result('YIELD_MALFORMED')
    # Both dictionaries contain only validated immutable scalar field values.
    s, c = dict(saved), dict(current)
    frame = s['frame_id']
    if any(s[k] != c[k] for k in ('session', 'frame_id', 'level')):
        return _result('YIELD_SCOPE', frame)
    if c['task_active'] is False:
        return _result('CANCELED', frame)
    if c['interrupt_resolved'] is False:
        return _result('WAIT_INTERRUPT', frame)
    if c['pending_result'] == 'UNKNOWN':
        return _result('RECONCILE_RESULT', frame)
    if c['source_fresh'] is False or c['source_generation'] != s['source_generation']:
        return _result('YIELD_STALE', frame)
    if c['queue_version'] != s['queue_version']:
        return _result('REPLAN_QUEUE', frame)
    if any(c[k] != s[k] for k in ('target_token', 'target_xid')):
        return _result('REVALIDATE_TARGET', frame)
    return _result('RESUME', frame)


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON member')
        result[key] = value
    return result


def _no_constant(text: str) -> object:
    raise ValueError('nonfinite JSON constant')


def decide_json(raw: object) -> dict[str, Any]:
    """One UTF-8 JSON object, two receipt members, no duplicate names/constants."""
    if type(raw) is not bytes or len(raw) > MAX_WIRE_BYTES:
        return _result('YIELD_MALFORMED')
    try:
        message = json.loads(raw.decode('utf-8', errors='strict'),
                             object_pairs_hook=_unique_object,
                             parse_constant=_no_constant)
        if type(message) is not dict or set(message) != {'saved', 'current'}:
            return _result('YIELD_MALFORMED')
        return decide(message['saved'], message['current'])
    except (UnicodeError, ValueError, TypeError, RecursionError, OverflowError):
        return _result('YIELD_MALFORMED')
