"""Preserve unavailable decoding; a pixel predicate is not saved-file truth."""
def visible_row_predicate(decoded, expected):
    if decoded is None:
        return 'unknown'
    if (type(decoded) is not list or len(decoded) != 3 or
            any(type(v) is not str or not v or not v.isascii() or not v.isdigit() for v in decoded)):
        return 'unknown'
    return decoded == expected
