"""Small independent PNG decoder for 8-bit RGB/RGBA, non-interlaced captures."""
import struct
import zlib


def decode_rgb(data: bytes, x: int, y: int, w: int, h: int):
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("bad PNG signature")
    pos = 8
    compressed = bytearray()
    width = height = color_type = None
    while pos < len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        kind = data[pos + 4 : pos + 8]
        chunk = data[pos + 8 : pos + 8 + length]
        pos += 12 + length
        if kind == b"IHDR":
            width, height, depth, color_type, compression, filtering, interlace = struct.unpack(
                ">IIBBBBB", chunk
            )
            if depth != 8 or color_type not in (2, 6) or compression or filtering or interlace:
                raise ValueError("unsupported PNG format")
        elif kind == b"IDAT":
            compressed.extend(chunk)
        elif kind == b"IEND":
            break
    if width is None:
        raise ValueError("missing IHDR")
    bpp = 3 if color_type == 2 else 4
    if x < 0 or y < 0 or x + w > width or y + h > height:
        raise ValueError("region outside image")
    raw = zlib.decompress(compressed)
    stride = width * bpp
    rows = []
    prior = bytearray(stride)
    offset = 0
    target_y = y + h // 2
    target_x = (x + w // 2) * bpp
    for _ in range(height):
        filt = raw[offset]
        scan = bytearray(raw[offset + 1 : offset + 1 + stride])
        offset += stride + 1
        for i in range(target_x + 3 if len(rows) <= target_y else 0):
            a = scan[i - bpp] if i >= bpp else 0
            b = prior[i]
            c = prior[i - bpp] if i >= bpp else 0
            if filt == 1:
                scan[i] = (scan[i] + a) & 255
            elif filt == 2:
                scan[i] = (scan[i] + b) & 255
            elif filt == 3:
                scan[i] = (scan[i] + ((a + b) // 2)) & 255
            elif filt == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if pa <= pb and pa <= pc else b if pb <= pc else c
                scan[i] = (scan[i] + pr) & 255
            elif filt != 0:
                raise ValueError(f"unsupported PNG filter {filt}")
        if len(rows) <= target_y:
            rows.append(scan)
            prior = scan
    return width, height, bpp, rows


def region_label(data: bytes, box, allowed):
    x, y, w, h = (box[k] for k in ("x", "y", "width", "height"))
    width, height, bpp, rows = decode_rgb(data, x, y, w, h)
    allowed_set = {tuple(c) for c in allowed}
    target_y = y + h // 2
    target_x = (x + w // 2) * bpp
    rgb = tuple(rows[target_y][target_x : target_x + 3])
    if rgb not in allowed_set:
        return "unresolved"
    return "rgb:" + ",".join(map(str, rgb))
