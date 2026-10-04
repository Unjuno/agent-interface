"""Small read-only Xlib bridge and private fixture painting, no input API."""
import ctypes as C
import ctypes.util
import time


class X11:
    def __init__(self, display):
        self.lib = C.CDLL(ctypes.util.find_library("X11"))
        bindings = {
            "XOpenDisplay": (C.c_void_p, [C.c_char_p]),
            "XCloseDisplay": (C.c_int, [C.c_void_p]),
            "XDefaultRootWindow": (C.c_ulong, [C.c_void_p]),
            "XCreateSimpleWindow": (C.c_ulong, [C.c_void_p, C.c_ulong, C.c_int, C.c_int, C.c_uint, C.c_uint, C.c_uint, C.c_ulong, C.c_ulong]),
            "XMapWindow": (C.c_int, [C.c_void_p, C.c_ulong]),
            "XCreateGC": (C.c_void_p, [C.c_void_p, C.c_ulong, C.c_ulong, C.c_void_p]),
            "XSetForeground": (C.c_int, [C.c_void_p, C.c_void_p, C.c_ulong]),
            "XFillRectangle": (C.c_int, [C.c_void_p, C.c_ulong, C.c_void_p, C.c_int, C.c_int, C.c_uint, C.c_uint]),
            "XSync": (C.c_int, [C.c_void_p, C.c_int]),
            "XGetImage": (C.c_void_p, [C.c_void_p, C.c_ulong, C.c_int, C.c_int, C.c_uint, C.c_uint, C.c_ulong, C.c_int]),
            "XGetPixel": (C.c_ulong, [C.c_void_p, C.c_int, C.c_int]),
            "XDestroyImage": (C.c_int, [C.c_void_p]),
            "XQueryKeymap": (C.c_int, [C.c_void_p, C.c_void_p]),
        }
        for name, (result, args) in bindings.items():
            fn = getattr(self.lib, name)
            fn.restype, fn.argtypes = result, args
        self.d = self.lib.XOpenDisplay(display.encode())
        if not self.d:
            raise RuntimeError("private X display unavailable")

    def make_window(self):
        w = self.lib.XCreateSimpleWindow(self.d, self.lib.XDefaultRootWindow(self.d), 0, 0, 32, 32, 0, 0, 0)
        self.lib.XMapWindow(self.d, w)
        self.lib.XSync(self.d, 0)
        gc = self.lib.XCreateGC(self.d, w, 0, None)
        return w, gc

    def paint(self, w, gc, identity, color):
        start = time.monotonic_ns()
        self.lib.XSetForeground(self.d, gc, color)
        self.lib.XFillRectangle(self.d, w, gc, 0, 0, 32, 32)
        self.lib.XSetForeground(self.d, gc, identity)
        self.lib.XFillRectangle(self.d, w, gc, 0, 0, 1, 1)
        self.lib.XSync(self.d, 0)
        return start, time.monotonic_ns()

    def capture(self, w):
        start = time.monotonic_ns()
        im = self.lib.XGetImage(self.d, w, 0, 0, 32, 32, C.c_ulong(-1).value, 2)
        returned = time.monotonic_ns()
        if not im:
            raise RuntimeError("XGetImage returned NULL")
        try:
            pixels = [self.lib.XGetPixel(im, x, y) for y in range(32) for x in range(32)]
        finally:
            self.lib.XDestroyImage(im)
        return start, returned, time.monotonic_ns(), pixels

    def keymap(self):
        buf = C.create_string_buffer(32)
        self.lib.XQueryKeymap(self.d, buf)
        return buf.raw.hex()

    def close(self):
        if self.d:
            self.lib.XCloseDisplay(self.d)
            self.d = None
