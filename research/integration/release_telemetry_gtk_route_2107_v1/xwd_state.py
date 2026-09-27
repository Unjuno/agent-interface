"""Candidate XWD state reader. The audit independently reimplements parsing."""
import struct


def classify(path):
    data = path.read_bytes()
    if len(data) < 100:
        raise ValueError("short_xwd")
    h = struct.unpack(">25I", data[:100])
    header, version, fmt, depth, width, height = h[:6]
    byte_order, bpp, stride = h[7], h[11], h[12]
    if version != 7 or fmt != 2 or width < 350 or height < 150 or bpp not in (24, 32):
        raise ValueError("unsupported_xwd")
    start = header + h[19] * 12
    if stride < width * (bpp // 8) or start + stride * height > len(data):
        raise ValueError("truncated_xwd")
    size = bpp // 8
    endian = "little" if byte_order == 0 else "big"
    masks = h[14:17]
    observed = []
    for x, y in ((5, 5), (10, 10), (20, 20), (30, 30), (width - 6, height - 6)):
        offset = start + y * stride + x * size
        value = int.from_bytes(data[offset:offset + size], endian)
        observed.append(value & (masks[0] | masks[1] | masks[2]))
    if all(x == observed[0] for x in observed) and observed[0] != 0:
        def component(mask):
            shift = (mask & -mask).bit_length() - 1
            return (observed[0] & mask) >> shift

        green = component(masks[1])
        red = component(masks[0])
        if green > red:
            return "DONE"
        if red > green:
            return "PENDING"
    raise ValueError("ambiguous_fixture_pixels")
