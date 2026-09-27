"""Research-only pre-rounding validity enclosure. No action authority."""
from fractions import Fraction
import math
import struct


def bits(value: float) -> int:
    return struct.unpack('>I', struct.pack('>f', value))[0]


def number(code: int) -> float:
    return struct.unpack('>f', struct.pack('>I', code))[0]


def cell(value: float) -> tuple[Fraction, Fraction]:
    """Closed conservative round-to-nearest binary32 preimage (ties included)."""
    if type(value) is not float or not math.isfinite(value) or abs(value) > 4:
        raise ValueError('UNSUPPORTED_INPUT')
    code = bits(value)
    if number(code) != value:
        raise ValueError('NOT_BINARY32')
    if value == 0:
        below, above = -number(1), number(1)
    elif value > 0:
        below, above = number(code-1), number(code+1)
    else:
        below, above = number(code+1), number(code-1)
    point = Fraction(value)
    return (Fraction(below)+point)/2, (point+Fraction(above))/2


def allowed(values: list[float]) -> bool:
    """True only when every source point in the rounding box meets the contract."""
    if type(values) is not list or len(values) != 4:
        return False
    try:
        (pl, ph), (vl, vh), (_, ah), (sl, _) = map(cell, values)
    except (ValueError, OverflowError, TypeError, struct.error):
        return False
    return (pl >= -Fraction(11, 10) and ph <= Fraction(11, 10)
            and vl >= -Fraction(7, 20) and vh <= Fraction(7, 20)
            and ah <= Fraction(9, 10) and sl >= Fraction(1, 2))
