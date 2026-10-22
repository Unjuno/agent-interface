"""One-shot source-level composition probe for exact PR #7429/#7449 snapshots."""
from __future__ import annotations
import importlib.util
import json
import sys
import types
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
P7429 = HERE / "source_snapshots" / "pr7429"
P7449 = HERE / "source_snapshots" / "pr7449"
sys.path[:0] = [str(P7429), str(P7449)]

# The probe exercises wrapper logic only; Xlib names are needed at import time,
# but the owner thread and any Xlib calls are never started.
def install_xlib_import_stubs():
    xlib = types.ModuleType("Xlib")
    xlib.X = types.SimpleNamespace(KeyPress=2, KeyRelease=3, ButtonRelease=5,
                                   Button1Mask=256, AnyPropertyType=0)
    xk = types.ModuleType("Xlib.XK")
    xk.string_to_keysym = lambda _key: 1
    display = types.ModuleType("Xlib.display")
    display.Display = lambda _name: (_ for _ in ()).throw(AssertionError("display must not start"))
    error = types.ModuleType("Xlib.error")
    error.BadWindow = type("BadWindow", (Exception,), {})
    error.BadDrawable = type("BadDrawable", (Exception,), {})
    ext = types.ModuleType("Xlib.ext")
    xtest = types.ModuleType("Xlib.ext.xtest")
    xtest.fake_input = lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("input must not run"))
    ext.xtest = xtest
    xlib.XK, xlib.display, xlib.error, xlib.ext = xk, display, error, ext
    sys.modules.update({"Xlib": xlib, "Xlib.X": types.ModuleType("Xlib.X"),
        "Xlib.XK": xk, "Xlib.display": display, "Xlib.error": error,
        "Xlib.ext": ext, "Xlib.ext.xtest": xtest})


def load_from(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

install_xlib_import_stubs()
import input_owner_v10
import input_owner_v11
input_owner_v13 = load_from(P7429 / "input_owner_v13.py", "input_owner_v13")

class Lease:
    deadline = 1000
    intent_token = "lease-v13"
    class Cancel:
        def is_set(self): return False
    cancel = Cancel()
    focus_invalid = False

# Exact v13 class + exact inherited v11 call wrapper; the fake v10 call models
# its documented None-returning owner completion and performs no Xlib action.
owner = object.__new__(input_owner_v13.InputOwner)
owner.owner_id = "owner-v13"
with patch.object(input_owner_v10.InputOwner, "call", return_value=None), \
     patch("input_owner_v11.time.perf_counter_ns", side_effect=[100, 145]):
    rpc = owner.call("up", Lease(), "space")

# Load the exact PR #7449 transition layers. Stub only the constructor's default
# v12 owner so that the tested injected object is shaped exactly like v13's RPC.
v12_stub = types.ModuleType("input_owner_v12")
v12_stub.InputOwner = type("UnusedV12", (), {})
sys.modules["input_owner_v12"] = v12_stub
transition_v3 = load_from(P7449 / "input_transition_owner_v3.py", "input_transition_owner_v3")
transition_v4 = load_from(P7449 / "input_transition_owner_v4.py", "input_transition_owner_v4")

class V13RPCShape:
    owner_id = "owner-v13"
    records = []
    def __init__(self, _display_name): pass
    def call(self, operation, lease=None, key=None):
        assert operation == "up" and key == "space"
        return dict(rpc)
    def close(self): pass

wrapper = transition_v4.InputOwner("fake-display", _owner_cls=V13RPCShape)
try:
    wrapper.call("up", Lease(), "space")
except BaseException as exc:
    integration = {"raised_type": type(exc).__name__, "raised_message": str(exc)}
else:
    integration = {"raised_type": None, "raised_message": None}

raw = {
    "probe_id": "V13-V4-EXPLICIT-UP-COMPOSITION-C01",
    "classification": "one-shot wrapper-composition construction; no owner thread or Xlib calls",
    "v13_call_result": rpc,
    "v4_integration_result": integration,
    "xlib_display_started": False,
    "xlib_input_called": False,
    "tries": 1,
}
(HERE / "RAW.json").write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(raw, sort_keys=True))
