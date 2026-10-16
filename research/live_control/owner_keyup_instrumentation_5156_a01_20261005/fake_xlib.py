"""Minimal deterministic Xlib substitute for the owner-thread construction rung."""
import sys
import types


class FakeServer:
    def __init__(self):
        self.down = set()
        self.calls = []
        self.sync_calls = 0
        self.fail_sync_at = None
        self.focus = 9
        self.closed = False


class FakeDisplay:
    def __init__(self, server):
        self.server = server
        self.root = types.SimpleNamespace(query_pointer=lambda: types.SimpleNamespace(mask=0, root_x=5, root_y=6))

    def screen(self): return types.SimpleNamespace(root=self.root)
    def get_input_focus(self): return types.SimpleNamespace(focus=self.server.focus)
    def keysym_to_keycode(self, value): return {"A": 38, "B": 56, "C": 54}.get(value, 0)
    def query_keymap(self):
        bitmap = bytearray(32)
        for code in self.server.down: bitmap[code // 8] |= 1 << (code % 8)
        return bytes(bitmap)
    def sync(self):
        self.server.sync_calls += 1
        self.server.calls.append(["sync", self.server.sync_calls])
        if self.server.fail_sync_at == self.server.sync_calls:
            raise RuntimeError("injected XSync failure")
    def close(self): self.server.closed = True


def install(server):
    xlib = types.ModuleType("Xlib")
    xlib.X = types.SimpleNamespace(KeyPress=2, KeyRelease=3, ButtonRelease=5, Button1Mask=256,
                                   AnyPropertyType=0, IsViewable=2, MotionNotify=6,
                                   ButtonPress=4)
    xlib.XK = types.SimpleNamespace(string_to_keysym=lambda key: key)
    display = types.ModuleType("Xlib.display")
    display.Display = lambda name: FakeDisplay(server)
    error = types.ModuleType("Xlib.error")
    class BadWindow(Exception): pass
    class BadDrawable(Exception): pass
    error.BadWindow, error.BadDrawable = BadWindow, BadDrawable
    xlib.display, xlib.error = display, error
    ext = types.ModuleType("Xlib.ext")
    xtest = types.ModuleType("Xlib.ext.xtest")
    def fake_input(d, event, detail=0, **kwargs):
        server.calls.append(["input", event, detail])
        if event == xlib.X.KeyPress: server.down.add(detail)
        elif event == xlib.X.KeyRelease: server.down.discard(detail)
    xtest.fake_input = fake_input
    ext.xtest = xtest
    sys.modules.update({"Xlib": xlib, "Xlib.display": display, "Xlib.error": error,
                       "Xlib.ext": ext, "Xlib.ext.xtest": xtest})

