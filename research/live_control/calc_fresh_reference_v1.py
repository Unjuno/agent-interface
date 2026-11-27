"""Bind an explicit target proposal to the latest post-action capture.

This mints an observational alias only. It does not verify the semantic meaning
of the proposal, grant input authority, run the GUI, or retry an uncertain mint.
The caller supplies a trusted bridge, reviewed proposal and same-clock boundary.
"""
import re
import time
from runtime.guarded_x11_v1.handles import ALIAS


def mint_from_proposal(bridge, proposal, *, scope, after_ns):
    unavailable = {'status': 'UNAVAILABLE', 'grants_input_authority': False,
                   'alias_may_be_consumed': False}
    if (type(proposal) is not dict or set(proposal) !=
            {'alias', 'source_sequence', 'source_sha256', 'point', 'region_size'} or
            type(scope) is not str or not scope or getattr(bridge, 'scope', None) != scope or
            type(after_ns) is not int or after_ns < 0):
        return unavailable
    revision = getattr(bridge, 'binding_revision', None)
    if (type(revision) is not int or revision < 0 or
            getattr(bridge, 'review_required', None) is not False or
            getattr(getattr(bridge, 'session', None), 'recovery_required', None) is not False or
            getattr(bridge, '_closed', False) is not False or getattr(bridge, 'active', None) is not None):
        return unavailable
    alias, sequence, digest = proposal['alias'], proposal['source_sequence'], proposal['source_sha256']
    point, size = proposal['point'], proposal['region_size']
    if (type(alias) is not str or ALIAS.fullmatch(alias) is None or
            type(sequence) is not int or sequence < 1 or sequence != getattr(bridge, 'sequence', None) or
            type(digest) is not str or not re.fullmatch(r'[0-9a-f]{64}', digest) or
            type(point) is not list or len(point) != 2 or any(type(x) is not int for x in point) or
            type(size) is not list or len(size) != 2 or any(type(x) is not int or x <= 0 for x in size)):
        return unavailable
    try:
        observation, image = bridge.history[sequence]
        capture = observation['capture_ns']
        native_digest = observation['native']['artifact']['sha256']
        now = time.monotonic_ns()
        x, y = point; w, h = size
        if (observation.get('sequence') != sequence or observation.get('binding_revision') != revision or
                type(capture) is not int or
                not after_ns < capture <= now or now - capture > 1_500_000_000 or
                native_digest != digest or x - w // 2 < 0 or y - h // 2 < 0 or
                x - w // 2 + w > image.width or y - h // 2 + h > image.height):
            return unavailable
    except (AttributeError, KeyError, TypeError, ValueError):
        return unavailable
    # Once mint is invoked its alias may be consumed, even if it raises or the
    # bridge association changes; never automatically retry it.
    unavailable = dict(unavailable, alias_may_be_consumed=True)
    try:
        minted = bridge.mint_reference(alias, sequence, list(point), region_size=tuple(size))
        if (getattr(bridge, 'sequence', None) != sequence or
                getattr(bridge, 'scope', None) != scope or
                getattr(bridge, 'binding_revision', None) != revision or
                getattr(bridge, 'review_required', None) is not False or
                getattr(getattr(bridge, 'session', None), 'recovery_required', None) is not False or
                getattr(bridge, '_closed', False) is not False or getattr(bridge, 'active', None) is not None or
                type(minted) is not dict or type(minted.get('offset')) is not list or
                len(minted['offset']) != 2 or any(type(x) is not int for x in minted['offset']) or
                type(minted.get('lifetime')) is not dict or
                minted['lifetime'].get('authority_granted') is not False):
            return unavailable
    except Exception:
        return unavailable
    return {'status': 'REFERENCE_MINTED', 'alias': alias, 'offset': list(minted['offset']),
            'source_sequence': sequence, 'source_sha256': digest,
            'grants_input_authority': False, 'alias_may_be_consumed': True}