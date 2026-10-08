from __future__ import annotations

NRES = 4
ALL_MASK = (1 << NRES) - 1

PARALLEL = 'PARALLEL'
SERIALIZE = 'SERIALIZE'
REVALIDATE = 'REVALIDATE'


def candidate(ra: int, wa: int, rb: int, wb: int, changed: int) -> str:
    vals = (ra, wa, rb, wb, changed)
    if any((not isinstance(x, int)) or x < 0 or x > ALL_MASK for x in vals):
        raise ValueError('mask')
    if (ra | rb) & changed:
        return REVALIDATE
    if wa & wb:
        return SERIALIZE
    if wa & rb:
        return SERIALIZE
    if wb & ra:
        return SERIALIZE
    return PARALLEL


def global_serial(*_args: int) -> str:
    return SERIALIZE


def write_only(ra: int, wa: int, rb: int, wb: int, changed: int) -> str:
    vals = (ra, wa, rb, wb, changed)
    if any((not isinstance(x, int)) or x < 0 or x > ALL_MASK for x in vals):
        raise ValueError('mask')
    if (ra | rb) & changed:
        return REVALIDATE
    if wa & wb:
        return SERIALIZE
    return PARALLEL


def hazard_flags(ra: int, wa: int, rb: int, wb: int, changed: int) -> dict[str, bool]:
    return {
        'stale_read': bool((ra | rb) & changed),
        'ww': bool(wa & wb),
        'a_write_b_read': bool(wa & rb),
        'b_write_a_read': bool(wb & ra),
    }
