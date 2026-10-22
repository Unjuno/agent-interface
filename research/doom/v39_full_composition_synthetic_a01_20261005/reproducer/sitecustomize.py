"""Synthetic seams for the isolated full controller/session construction test."""
import os
import json
import sys
import tempfile
import types
from pathlib import Path

os.environ.setdefault("DISPLAY", ":fake")

class FakeRoot:
    id = 1
    def query_pointer(self):
        return types.SimpleNamespace(mask=0, root_x=5, root_y=5)
    def get_full_property(self, atom, _kind):
        if atom in ("_NET_ACTIVE_WINDOW", 1):
            return types.SimpleNamespace(value=[41])
        return types.SimpleNamespace(value=[41])
    def translate_coords(self, _window, x, y):
        return types.SimpleNamespace(x=x, y=y)

class FakeWindow:
    def __init__(self, identifier): self.id = identifier
    def query_tree(self): return types.SimpleNamespace(parent=FakeRoot())
    def get_geometry(self): return types.SimpleNamespace(x=0, y=0, width=640, height=480)
    def get_attributes(self): return types.SimpleNamespace(map_state=2)

class FakeDisplay:
    def __init__(self):
        self.root = FakeRoot()
        self.down = set()
        self.closed = False
    def get_input_focus(self): return types.SimpleNamespace(focus=41)
    def screen(self): return types.SimpleNamespace(root=self.root)
    def intern_atom(self, name): return name
    def create_resource_object(self, _kind, identifier): return FakeWindow(identifier)
    def keysym_to_keycode(self, keysym): return int(keysym) % 240 + 8
    def get_geometry(self, _surface): return types.SimpleNamespace(width=640, height=480)
    def sync(self): pass
    def query_keymap(self):
        bitmap = bytearray(32)
        for code in self.down: bitmap[code // 8] |= 1 << (code % 8)
        return bytes(bitmap)
    def close(self): self.closed = True

_display = FakeDisplay()
x = types.ModuleType("Xlib.X")
x.KeyPress, x.KeyRelease, x.ButtonRelease = 2, 3, 5
x.Button1Mask, x.AnyPropertyType, x.IsViewable = 256, 0, 2
xk = types.ModuleType("Xlib.XK")
xk.string_to_keysym = lambda key: sum((i + 1) * ord(ch) for i, ch in enumerate(key))
display = types.ModuleType("Xlib.display")
display.Display = lambda _name=None: _display
error = types.ModuleType("Xlib.error")
error.BadWindow = type("BadWindow", (Exception,), {})
error.BadDrawable = type("BadDrawable", (Exception,), {})
ext = types.ModuleType("Xlib.ext")
xtest = types.ModuleType("Xlib.ext.xtest")
def fake_input(_display_obj, event, code):
    if event == x.KeyPress: _display.down.add(code)
    elif event == x.KeyRelease: _display.down.discard(code)
    trace = os.environ.get("V39_FAKE_X_TRACE")
    if trace:
        with open(trace, "a", encoding="utf-8") as stream:
            stream.write(json.dumps({"event": event, "keycode": code,
                                     "down_after": sorted(_display.down)}) + "\n")
xtest.fake_input = fake_input
ext.xtest = xtest
xlib = types.ModuleType("Xlib")
xlib.X, xlib.XK, xlib.display, xlib.error, xlib.ext = x, xk, display, error, ext
sys.modules.update({"Xlib": xlib, "Xlib.X": x, "Xlib.XK": xk,
                    "Xlib.display": display, "Xlib.error": error,
                    "Xlib.ext": ext, "Xlib.ext.xtest": xtest})

class FakeSession:
    def __init__(self):
        self.name = ":fake"
        self.d = _display
        self.tmp = Path(tempfile.mkdtemp(prefix="unjuno-fake-session-"))
        self.env = {key: "/tmp" for key in
                    ("DISPLAY", "XAUTHORITY", "HOME", "XDG_CONFIG_HOME",
                     "XDG_CACHE_HOME", "XDG_RUNTIME_DIR")}
        self.env["DISPLAY"] = self.name
    def _wait(self, predicate, _timeout, message):
        if not predicate(): raise RuntimeError(message)
    def windows(self): return "0x29 0 0 Doom Synthetic"
    def focus(self, _title): pass
    def context(self):
        return {"focus": 41, "surface": 41, "geometry": [0, 0, 640, 480]}
    def close(self): pass

gui = types.ModuleType("gui_suite")
gui.APPS = ["fake"]
gui.base = types.SimpleNamespace(X=x, XK=xk, xtest=xtest)
gui.Session = FakeSession
sys.modules["gui_suite"] = gui

class GameVariable:
    DEATHCOUNT, KILLCOUNT = 0, 1
class FakeGame:
    def __init__(self): self.tic = 0; self.finished = False; self.dead = False
    def __getattr__(self, name):
        if name.startswith("set_"): return lambda *args, **kwargs: None
        raise AttributeError(name)
    def init(self): pass
    def load(self, _path): pass
    def advance_action(self, _n=1, _update=True): self.tic += 1
    def get_episode_time(self): return self.tic
    def is_episode_finished(self): return self.finished
    def is_player_dead(self): return self.dead
    def get_game_variable(self, variable): return 0
    def get_ticrate(self): return 35
    def is_episode_timeout_reached(self): return False
    def get_mode(self): return "ASYNC_SPECTATOR"
    def get_total_reward(self): return 0
    def close(self): pass
vd = types.ModuleType("vizdoom")
vd.__version__ = "synthetic-1"
vd.__file__ = str(Path(tempfile.gettempdir()) / "fake_vizdoom" / "__init__.py")
Path(vd.__file__).parent.mkdir(parents=True, exist_ok=True)
(Path(vd.__file__).parent / "freedoom2.wad").write_bytes(b"synthetic-wad")
vd.DoomGame = FakeGame
vd.Mode = types.SimpleNamespace(ASYNC_SPECTATOR=0)
vd.ScreenResolution = types.SimpleNamespace(RES_640X480=0)
vd.Button = types.SimpleNamespace(TURN_LEFT=0, TURN_RIGHT=1, MOVE_FORWARD=2,
    MOVE_BACKWARD=3, MOVE_LEFT=4, MOVE_RIGHT=5, ATTACK=6, USE=7, SPEED=8)
vd.GameVariable = GameVariable
sys.modules["vizdoom"] = vd

class FakeStatusReader:
    def __init__(self, _wad, signal_id): self.signal_id = signal_id
    def read_frame(self, observation, _frame):
        value = 100 if self.signal_id == "health" else 50
        return {"format": "observable-signal-v1", "status": "observed",
                "signal_id": self.signal_id, "value": value,
                "sequence": observation["sequence"],
                "capture_ns": observation["capture_ns"],
                "binding": observation["pointer_binding"],
                "wad_sha256": "0" * 64}
    def read(self, observation):
        value = 100 if self.signal_id == "health" else 50
        return {"format": "observable-signal-v1", "status": "observed", "signal_id": self.signal_id,
                "value": value, "sequence": observation["sequence"],
                "capture_ns": observation["capture_ns"],
                "binding": observation["pointer_binding"],
                "wad_sha256": "0" * 64}
hud = types.ModuleType("doom_hud_signal_v3")
hud.DoomStatusNumberReader = FakeStatusReader
sys.modules["doom_hud_signal_v3"] = hud

from PIL import ImageGrab
ImageGrab.grab = lambda *args, **kwargs: __import__("PIL.Image", fromlist=["new"]).new("RGB", (640,480), (1,2,3))
