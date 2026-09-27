"""One research-only immutable-observation transaction on binary stdio."""
from fractions import Fraction as F
import math
import struct
import sys
from vendor import cell, allowed

HEADER = struct.Struct('>cQ')
PAYLOAD = {b'C': 16, b'D': 32, b'R': 0, b'V': 0, b'I': 0, b'U': 0, b'M': 0}


def classify_exact(values):
    if len(values) != 4 or any(not math.isfinite(v) or abs(v) > 4 for v in values):
        return b'U'
    p, v, a, s = map(F, values)
    return b'V' if abs(p) <= F(11, 10) and abs(v) <= F(7, 20) and a <= F(9, 10) and s >= F(1, 2) else b'I'


def classify_coarse(values):
    if allowed(list(values)):
        return b'V'
    try:
        (pl, ph), (vl, vh), (al, _), (_, sh) = map(cell, values)
    except (ValueError, OverflowError, TypeError, struct.error):
        return b'U'
    if ph < -F(11, 10) or pl > F(11, 10) or vh < -F(7, 20) or vl > F(7, 20) or al > F(9, 10) or sh < F(1, 2):
        return b'I'
    return b'U'


def read_exact(n):
    chunks = bytearray()
    while len(chunks) < n:
        part = sys.stdin.buffer.read(n - len(chunks))
        if not part:
            raise EOFError('incomplete frame')
        chunks.extend(part)
    return bytes(chunks)


def receive():
    kind, oid = HEADER.unpack(read_exact(9))
    if kind not in PAYLOAD:
        raise ValueError('unsupported frame')
    return kind, oid, read_exact(PAYLOAD[kind])


def send(kind, oid):
    sys.stdout.buffer.write(HEADER.pack(kind, oid))
    sys.stdout.buffer.flush()


def main(mode):
    kind, oid, payload = receive()
    if mode == 'ALWAYS64':
        result = classify_exact(struct.unpack('>4d', payload)) if kind == b'D' else b'U'
    else:
        if kind != b'C':
            send(b'U', oid)
            return
        result = classify_coarse(struct.unpack('>4f', payload))
        if result == b'U' and mode == 'SELECTIVE64':
            send(b'R', oid)
            rk, rid, fine = receive()
            result = b'U'
            if rk == b'D' and rid == oid:
                values = struct.unpack('>4d', fine)
                exact = classify_exact(values)
                if exact != b'U' and struct.pack('>4f', *values) == payload:
                    result = exact
    send(result, oid)


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ('COARSE_ONLY', 'ALWAYS64', 'SELECTIVE64'):
        raise SystemExit('expected COARSE_ONLY, ALWAYS64 or SELECTIVE64')
    main(sys.argv[1])
