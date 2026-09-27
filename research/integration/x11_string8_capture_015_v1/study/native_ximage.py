#!/usr/bin/env python3
"""Minimal independent libX11 XGetImage byte/pixel oracle using ctypes."""
import ctypes
import ctypes.util


class _ImageFunctions(ctypes.Structure):
    _fields_ = [(name, ctypes.c_void_p) for name in ("create_image", "destroy_image", "get_pixel", "put_pixel", "sub_image", "add_pixel")]


class _XImage(ctypes.Structure):
    _fields_ = [
        ("width", ctypes.c_int), ("height", ctypes.c_int), ("xoffset", ctypes.c_int), ("format", ctypes.c_int),
        ("data", ctypes.c_void_p), ("byte_order", ctypes.c_int), ("bitmap_unit", ctypes.c_int),
        ("bitmap_bit_order", ctypes.c_int), ("bitmap_pad", ctypes.c_int), ("depth", ctypes.c_int),
        ("bytes_per_line", ctypes.c_int), ("bits_per_pixel", ctypes.c_int),
        ("red_mask", ctypes.c_ulong), ("green_mask", ctypes.c_ulong), ("blue_mask", ctypes.c_ulong),
        ("obdata", ctypes.c_void_p), ("functions", _ImageFunctions),
    ]


def capture(drawable_id: int, width: int, height: int, display_name: str) -> dict:
    library_name = ctypes.util.find_library("X11")
    if not library_name:
        raise RuntimeError("libX11 was not found")
    x11 = ctypes.CDLL(library_name)
    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
    x11.XGetImage.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_int, ctypes.c_uint, ctypes.c_uint, ctypes.c_ulong, ctypes.c_int]
    x11.XGetImage.restype = ctypes.POINTER(_XImage)
    display = x11.XOpenDisplay(display_name.encode("ascii"))
    if not display:
        raise RuntimeError("native XOpenDisplay failed")
    image = None
    try:
        image = x11.XGetImage(display, drawable_id, 0, 0, width, height, 0xFFFFFFFF, 2)
        if not image:
            raise RuntimeError("native XGetImage returned NULL")
        view = image.contents
        raw = ctypes.string_at(view.data, view.bytes_per_line * view.height)
        metadata = {key: int(getattr(view, key)) for key in ("width", "height", "depth", "bits_per_pixel", "bytes_per_line", "byte_order")}
        get_pixel = ctypes.CFUNCTYPE(ctypes.c_ulong, ctypes.POINTER(_XImage), ctypes.c_int, ctypes.c_int)(view.functions.get_pixel)
        pixel_values = [int(get_pixel(image, x, y)) for y in range(height) for x in range(width)]
        destroy = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(_XImage))(view.functions.destroy_image)
        destroy(image)
        image = None
        return {"raw": raw, "pixels": pixel_values, **metadata}
    finally:
        if image:
            destroy = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(_XImage))(image.contents.functions.destroy_image)
            destroy(image)
        x11.XCloseDisplay(display)
