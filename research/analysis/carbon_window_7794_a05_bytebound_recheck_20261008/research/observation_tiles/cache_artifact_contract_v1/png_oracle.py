"""Independent bounded RGB8/noninterlaced PNG decoder. No Pillow import.
W3C PNG Third Edition, sections 5, 9, 11. Not a general PNG implementation.
"""
import struct
import zlib


def decode(data):
    if not isinstance(data, bytes) or not 8 <= len(data) <= 262144:
        raise ValueError('byte extent')
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('signature')
    offset, chunks, payload, geometry = 8, [], b'', None
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError('chunk truncated')
        length = struct.unpack('!I', data[offset:offset+4])[0]
        kind = data[offset+4:offset+8]
        end = offset+12+length
        if end > len(data):
            raise ValueError('chunk body truncated')
        content = data[offset+8:end-4]
        crc = struct.unpack('!I', data[end-4:end])[0]
        if zlib.crc32(kind+content) & 0xffffffff != crc:
            raise ValueError('CRC')
        if not chunks and kind != b'IHDR':
            raise ValueError('missing first IHDR')
        if kind == b'IHDR':
            if chunks or length != 13:
                raise ValueError('IHDR')
            w, h, depth, color, compression, filtering, interlace = struct.unpack('!IIBBBBB', content)
            if not (0 < w <= 128 and 0 < h <= 128) or (depth,color,compression,filtering,interlace) != (8,2,0,0,0):
                raise ValueError('outside RGB8 fixture contract')
            geometry = w, h
        elif kind == b'IDAT':
            if b'IEND' in chunks or (b'IDAT' in chunks and chunks[-1] != b'IDAT'):
                raise ValueError('IDAT order')
            payload += content
        elif kind == b'IEND':
            if length or b'IDAT' not in chunks or end != len(data):
                raise ValueError('IEND')
        elif kind != b'tEXt':
            raise ValueError('unsupported fixture chunk')
        chunks.append(kind)
        offset = end
    if not chunks or chunks[-1] != b'IEND' or geometry is None:
        raise ValueError('incomplete PNG')
    w, h = geometry
    stride = 3*w
    expected = (stride+1)*h
    inflater = zlib.decompressobj()
    filtered = inflater.decompress(payload, expected+1)
    if len(filtered) != expected or not inflater.eof or inflater.unused_data or inflater.unconsumed_tail:
        raise ValueError('deflate extent')
    pixels, previous = bytearray(), bytearray(stride)
    for y in range(h):
        kind = filtered[y*(stride+1)]
        if kind not in range(5):
            raise ValueError('filter')
        line = bytearray(stride)
        for i, value in enumerate(filtered[y*(stride+1)+1:(y+1)*(stride+1)]):
            left = line[i-3] if i >= 3 else 0
            above = previous[i]
            corner = previous[i-3] if i >= 3 else 0
            if kind == 0:
                predictor = 0
            elif kind == 1:
                predictor = left
            elif kind == 2:
                predictor = above
            elif kind == 3:
                predictor = (left+above)//2
            else:
                estimate = left+above-corner
                distances = (abs(estimate-left), abs(estimate-above), abs(estimate-corner))
                predictor = (left, above, corner)[distances.index(min(distances))]
            line[i] = (value+predictor) % 256
        pixels.extend(line)
        previous = line
    return w, h, bytes(pixels)
