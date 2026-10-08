"""Research-only range lowering; no focus, lease, composition or action authority."""
import hashlib


def lower(context_text, current_text, span, unit):
    if hashlib.sha256(context_text.encode('utf-8')).digest() != hashlib.sha256(current_text.encode('utf-8')).digest():
        raise ValueError('STALE_SOURCE')
    if not isinstance(span, list) or len(span) != 2 or any(type(x) is not int for x in span):
        raise ValueError('INVALID_RANGE')
    if unit == 'unicode_scalar':
        if any(x < 0 or x > len(context_text) for x in span):
            raise ValueError('INVALID_RANGE')
        return [len(context_text[:x].encode('utf-16-le')) // 2 for x in span]
    if unit == 'utf16':
        boundaries = {len(context_text[:x].encode('utf-16-le')) // 2 for x in range(len(context_text) + 1)}
        if any(x not in boundaries for x in span):
            raise ValueError('INVALID_UTF16_BOUNDARY')
        return list(span)
    raise ValueError('UNKNOWN_UNIT')
