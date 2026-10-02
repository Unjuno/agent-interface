"""No-input construction check for the private Xvfb fixture and runtime imports."""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from experiment import REPO, xvfb_pid
sys.path.insert(0, str(REPO))
from Xlib import display
from runtime.backends.x11_v1.backend import X11Backend
from runtime.backends.x11_v1.session import X11RuntimeSession


def main():
    with tempfile.TemporaryDirectory(prefix="ai-2437-preflight-") as tmp:
        meta = Path(tmp) / "meta.json"
        fixture = subprocess.Popen([
            sys.executable, "-m", "runtime.backends.x11_v1.fixture_app",
            "--meta", str(meta), "--effect", str(Path(tmp) / "effect.json"),
        ], cwd=REPO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        backend = observer = None
        try:
            deadline = time.monotonic() + 8
            while not meta.exists() and time.monotonic() < deadline:
                if fixture.poll() is not None:
                    raise RuntimeError(f"fixture exited {fixture.returncode}")
                time.sleep(.02)
            if not meta.exists():
                raise RuntimeError("fixture metadata timeout")
            window = int(json.loads(meta.read_text())["window_id"])
            backend = X11Backend(os.environ["DISPLAY"], {"fixture": window})
            session = X11RuntimeSession(backend)
            observer = display.Display(os.environ["DISPLAY"])
            keymap = observer.query_keymap()
            print(json.dumps({
                "display": os.environ["DISPLAY"],
                "xvfb_pid": xvfb_pid(os.environ["DISPLAY"]),
                "fixture_pid": fixture.pid,
                "window_id": window,
                "keymap_bytes": len(keymap),
                "backend_emissions": backend.emissions,
                "session_recovery_required": session.recovery_required,
            }, sort_keys=True))
        finally:
            if backend is not None:
                backend.close()
            if observer is not None:
                observer.close()
            if fixture.poll() is None:
                fixture.terminate()
                try:
                    fixture.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    fixture.kill()
                    fixture.wait(timeout=3)


if __name__ == "__main__":
    main()
