from __future__ import annotations

PARALLEL = 'PARALLEL'
SERIALIZE = 'SERIALIZE'
REVALIDATE = 'REVALIDATE'
MAX = 15


def oracle(ra: int, wa: int, rb: int, wb: int, changed: int) -> str:
    for x in (ra, wa, rb, wb, changed):
        if type(x) is not int or x < 0 or x > MAX:
            raise ValueError('invalid mask')
    read_union = ra | rb
    if changed & read_union:
        return REVALIDATE
    cross = (wa & wb) | (wa & rb) | (wb & ra)
    if cross:
        return SERIALIZE
    return PARALLEL
