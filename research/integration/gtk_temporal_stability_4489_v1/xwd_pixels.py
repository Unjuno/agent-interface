"""Minimal XWD ZPixmap reader used by the candidate and independent audit."""
import hashlib
import struct


def read_xwd(data):
    if len(data) < 100:
        raise ValueError("short_xwd_header")
    h = struct.unpack(">25I", data[:100])
    header_size, version, fmt, depth, width, height = h[:6]
    byte_order, bpp, stride = h[7], h[11], h[12]
    red_mask, green_mask, blue_mask, ncolors = h[14], h[15], h[16], h[19]
    if version != 7 or fmt != 2 or width <= 0 or height <= 0 or bpp not in (24, 32):
        raise ValueError("unsupported_xwd_format")
    if stride < width * ((bpp + 7) // 8):
        raise ValueError("invalid_xwd_stride")
    start = header_size + ncolors * 12
    if start + stride * height > len(data):
        raise ValueError("truncated_xwd_pixels")
    endian = "little" if byte_order == 0 else "big"
    size = bpp // 8
    pixels = []
    for y in range(height):
        row = []
        offset = start + y * stride
        for x in range(width):
            raw = int.from_bytes(data[offset + x * size:offset + (x + 1) * size], endian)
            row.append(raw)
        pixels.append(row)
    return {"width": width, "height": height, "depth": depth, "bpp": bpp,
            "stride": stride, "masks": [red_mask, green_mask, blue_mask],
            "pixels": pixels, "sha256": hashlib.sha256(data).hexdigest()}


def changed_pixels(left, right):
    if (left["width"], left["height"]) != (right["width"], right["height"]):
        raise ValueError("xwd_dimensions_differ")
    coords = [(x, y) for y, (a, b) in enumerate(zip(left["pixels"], right["pixels"]))
              for x, (pa, pb) in enumerate(zip(a, b)) if pa != pb]
    if not coords:
        box = None
    else:
        xs, ys = zip(*coords)
        box = [min(xs), min(ys), max(xs), max(ys)]
    return {"count": len(coords), "bbox": box, "coords": coords}


def volatile_pixels(calibration_images):
    if not calibration_images:
        raise ValueError("empty_calibration")
    volatile = set()
    for image in calibration_images[1:]:
        d = changed_pixels(calibration_images[0], image)
        volatile.update(d["coords"])
    return volatile


def volatile_mask(calibration_images, halo=1):
    volatile = volatile_pixels(calibration_images)
    width, height = calibration_images[0]["width"], calibration_images[0]["height"]
    expanded = set()
    for x, y in volatile:
        for dy in range(-halo, halo + 1):
            for dx in range(-halo, halo + 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    expanded.add((nx, ny))
    return expanded
