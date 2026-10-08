"""Private import-namespace adapter for Issue #1962.

This module performs no GUI, X11, model, or MAP01 work. It only loads the
retained live-control backend under its intended module identities while the
Doom entrypoint remains outside the live-control search path.
"""
from contextlib import contextmanager
import importlib
import importlib.util
import sys
from pathlib import Path

_LIVE_NAMES = tuple(f"session_v{i}" for i in range(4, 11))


@contextmanager
def live_control_backend(repo_root: Path):
    live = (repo_root / "research" / "live_control").resolve()
    doom = (repo_root / "research" / "doom").resolve()
    old_path = list(sys.path)
    old_modules = {name: sys.modules.get(name) for name in _LIVE_NAMES}
    sys.path[:] = [str(live), str(doom)] + [p for p in old_path if p not in (str(live), str(doom))]
    try:
        # Install the intended live-control session_v7 under the bare name that
        # session_v8 imports. The Doom entrypoint is never loaded as session_v7.
        path = live / "session_v7.py"
        spec = importlib.util.spec_from_file_location("session_v7", path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot create spec for {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules["session_v7"] = module
        spec.loader.exec_module(module)
        v8 = importlib.import_module("session_v8")
        if Path(v8.__file__).resolve() != live / "session_v8.py":
            raise AssertionError(f"wrong session_v8 origin: {v8.__file__}")
        if Path(sys.modules["session_v7"].__file__).resolve() != live / "session_v7.py":
            raise AssertionError("session_v7 resolved outside live_control")
        yield v8
    finally:
        sys.path[:] = old_path
        for name, previous in old_modules.items():
            if previous is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous