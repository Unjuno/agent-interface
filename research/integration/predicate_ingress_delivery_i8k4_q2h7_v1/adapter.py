"""Opt-in typed ingress for the exact #4236 research predicate; no OS authority.

Only handle_wire(bytes) is the supported public entry. Extra current-state fields
are ignored, consistent with the predecessor's declared dependency assumption.
"""
from __future__ import annotations
import json
import math
from typing import Any
from provenance import upstream

MAX_WIRE_BYTES = 65536
MAX_CONTAINER_DEPTH = 32
GENERATIONS = ('form_generation', 'required_form_generation', 'intent_version',
               'producer_version', 'source_generation')
STATE_KEYS = frozenset((*GENERATIONS, 'source_current', 'intent'))


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise ValueError('duplicate key')
        out[key] = value
    return out


def _constant(_: str) -> None:
    raise ValueError('nonfinite number')


def _bounded_tree(value: Any) -> None:
    pending = [(value, 0)]
    while pending:
        item, depth = pending.pop()
        if isinstance(item, (dict, list)):
            depth += 1
            if depth > MAX_CONTAINER_DEPTH:
                raise ValueError('container depth')
            children = item.values() if isinstance(item, dict) else item
            pending.extend((child, depth) for child in children)
        elif isinstance(item, float) and not math.isfinite(item):
            raise ValueError('float overflow')


def _valid_state(state: Any) -> bool:
    return (type(state) is dict and STATE_KEYS <= state.keys()
            and all(type(state[key]) is int and state[key] >= 0 for key in GENERATIONS)
            and type(state['source_current']) is bool
            and type(state['intent']) is str and state['intent'] in ('submit', 'inspect'))


def _valid_artifact(artifact: Any) -> bool:
    # Check hashability/type before the exact predecessor's set membership calls.
    if type(artifact) is not dict or artifact.keys() != {'schema', 'predicate', 'value', 'key', 'digest'}:
        return False
    if any(type(artifact[key]) is not str for key in ('schema', 'predicate', 'value', 'digest')):
        return False
    key = artifact['key']
    if not _valid_state(key) or key.keys() != STATE_KEYS:
        return False
    return upstream.valid_artifact(artifact)


def _response(status: str, result: Any = None, artifact_status: str | None = None) -> dict[str, Any]:
    return {'schema': 'agent-interface/predicate-ingress-i8k4-v1',
            'status': status, 'artifact_status': artifact_status, 'result': result,
            'authority': 'none', 'input_dispatched': False, 'task_success': None}


def handle_wire(raw: bytes) -> dict[str, Any]:
    """Return typed invalid evidence or an unchanged research result.

    No coercion of generations, currentness or intent is performed. A malformed
    cache is a miss only when the current-state/request/wire contracts are valid.
    The nested legacy 'executable' field is a predicate diagnostic, not permission.
    """
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_WIRE_BYTES:
        return _response('INVALID_WIRE')
    try:
        request = json.loads(raw.decode('utf-8'), object_pairs_hook=_object,
                             parse_constant=_constant)
        _bounded_tree(request)
    except (ValueError, UnicodeError, RecursionError):
        return _response('INVALID_WIRE')
    if type(request) is not dict or type(request.get('op')) is not str:
        return _response('INVALID_REQUEST')
    op = request['op']
    if op == 'prepare':
        if request.keys() != {'op', 'state'}:
            return _response('INVALID_REQUEST')
    elif op == 'consume':
        if (request.keys() != {'op', 'policy', 'artifact', 'state'}
                or request['policy'] != 'DEPENDENCY_BOUND_PERSIST'):
            return _response('INVALID_REQUEST')
    else:
        return _response('INVALID_REQUEST')
    state = request['state']
    if not _valid_state(state):
        return _response('INVALID_CURRENT_STATE')
    if op == 'prepare':
        return _response('PREPARED', upstream.prepare(state))
    valid = _valid_artifact(request['artifact'])
    # Deliberately keep upstream.consume unchanged, including its recomputation
    # for oracle/correct diagnostics. No compute-elision benefit is asserted.
    result = upstream.consume('DEPENDENCY_BOUND_PERSIST', request['artifact'] if valid else None, state)
    return _response('OK', result, 'VALID' if valid else 'INVALID_OR_ABSENT')
