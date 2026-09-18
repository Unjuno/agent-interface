from __future__ import annotations

MUST_FORWARD_FAMILIES={
    'SINGLE_PIXEL','STATUS_DOT_2X2','CURSOR_1X3','GLYPH_STROKE_1X4','LOCAL_BLOCK_4X4','HASH_FLIP'
}

def exact_semantic_oracle(family: str, base_repr: tuple, changed_repr: tuple) -> dict:
    exact_equal = base_repr == changed_repr
    must_forward = family in MUST_FORWARD_FAMILIES
    if family == 'UNCHANGED' and not exact_equal:
        raise ValueError('unchanged_not_equal')
    if must_forward and exact_equal:
        raise ValueError('must_forward_not_changed')
    return {'exact_equal': exact_equal, 'must_forward': must_forward}
