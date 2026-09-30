"""Non-formal Docker diagnostic: compare Tk fixture input with/without Entry click."""
from __future__ import annotations

import json
import os
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from Xlib.display import Display
from runtime.backends.x11_v1.backend import X11Backend
from runtime.backends.x11_v1.session import X11RuntimeSession


def run_case(click_entry: bool) -> dict:
    with tempfile.TemporaryDirectory(prefix="x11-fixture-diagnostic-") as temp:
        root = Path(temp)
        log = (root / "xvfb.log").open("wb")
        server = subprocess.Popen(
            ["Xvfb", "-displayfd", "1", "-screen", "0", "1024x768x24", "-nolisten", "tcp", "-noreset"],
            stdout=subprocess.PIPE, stderr=log, text=True, bufsize=1,
        )
        fixture = backend = anchor = None
        try:
            ready, _, _ = select.select([server.stdout], [], [], 8)
            display = ":" + server.stdout.readline().strip() if ready else ""
            if not display[1:].isdecimal():
                raise RuntimeError("Xvfb did not report a display")
            anchor = Display(display)
            subprocess.run(["setxkbmap", "-display", display, "-layout", "us"], check=True)
            meta, effect, events = (root / name for name in ("meta.json", "effect.json", "events.jsonl"))
            fixture = subprocess.Popen(
                [sys.executable, "-m", "runtime.backends.x11_v1.fixture_app", "--meta", str(meta),
                 "--effect", str(effect), "--events", str(events)],
                env=os.environ | {"DISPLAY": display}, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            deadline = time.monotonic() + 8
            while not meta.exists() and fixture.poll() is None and time.monotonic() < deadline:
                time.sleep(0.02)
            if not meta.exists():
                raise RuntimeError(f"fixture failed to create metadata: {fixture.stderr.read()}")
            window = json.loads(meta.read_text())["window_id"]
            backend = X11Backend(display, {"fixture": window})
            session = X11RuntimeSession(backend)
            ops = [{"op": "focus", "target": "fixture"}]
            if click_entry:
                ops.extend([
                    {"op": "pointer_move", "target": "fixture", "frame": "window_client", "x": 50, "y": 55},
                    {"op": "pointer_button", "button": "left", "down": True},
                    {"op": "pointer_button", "button": "left", "down": False},
                ])
            ops.extend([
                {"op": "text", "text": "a"},
                {"op": "key_chord", "keys": ["CTRL", "S"]},
                {"op": "release_all"},
            ])
            program = {
                "schema": "agent-interface/program-v1", "program_id": "docker-diagnostic-click" if click_entry else "docker-diagnostic-focus-only",
                "source": {"observation_seq": 7, "binding_revision": 3},
                "authority": {"lease_id": "docker-diagnostic", "expires_at_ns": time.monotonic_ns() + 30_000_000_000},
                "terminal": {"release_all_required": True}, "ops": ops,
            }
            dispatch = session.dispatch(program, current_observation_seq=7, current_binding_revision=3)
            return {
                "click_entry": click_entry, "dispatch_status": dispatch.get("status"),
                "dispatch": dispatch,
                "saved_effect": effect.read_text() if effect.exists() else None,
                "events": events.read_text() if events.exists() else None,
                "completed_ops": dispatch.get("execution", {}).get("completed_ops"),
                "release_verified": dispatch.get("execution", {}).get("releases", [{}])[-1].get("verified"),
            }
        finally:
            if backend is not None:
                backend.close()
            if fixture is not None and fixture.poll() is None:
                fixture.terminate()
                fixture.wait(timeout=3)
            if anchor is not None:
                anchor.close()
            if server.poll() is None:
                server.terminate()
                server.wait(timeout=3)
            if server.stdout:
                server.stdout.close()
            log.close()


if __name__ == "__main__":
    print(json.dumps({"scope": "non-formal local Docker fixture diagnostic", "cases": [run_case(False), run_case(True)]}, sort_keys=True))
