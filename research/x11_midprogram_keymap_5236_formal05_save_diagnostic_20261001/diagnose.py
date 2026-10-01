"""Nonformal Docker diagnostic of #5236 formal05 save/effect timing and key events."""
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

WAIT_MS = 1500


def run_case(inter_op_wait: bool) -> dict:
    case = "ctrl_s_wait_update_250ms" if inter_op_wait else "ctrl_s_then_release"
    with tempfile.TemporaryDirectory(prefix="issue5236-save-diag-") as temp:
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
                raise RuntimeError("fixture did not create metadata")
            window = json.loads(meta.read_text(encoding="utf-8"))["window_id"]
            backend = X11Backend(display, {"fixture": window})
            session = X11RuntimeSession(backend)
            ops = [
                {"op": "focus", "target": "fixture"},
                {"op": "pointer_move", "target": "fixture", "frame": "window_client", "x": 50, "y": 55},
                {"op": "pointer_button", "button": "left", "down": True},
                {"op": "pointer_button", "button": "left", "down": False},
                {"op": "text", "text": "a"},
                {"op": "wait_update", "timeout_ms": WAIT_MS},
                {"op": "text", "text": "_"},
                {"op": "key_chord", "keys": ["CTRL", "S"]},
            ]
            if inter_op_wait:
                ops.append({"op": "wait_update", "timeout_ms": 250})
            ops.append({"op": "release_all"})
            program = {
                "schema": "agent-interface/program-v1",
                "program_id": "issue5236-formal05-save-diag-" + case,
                "source": {"observation_seq": 7, "binding_revision": 3},
                "authority": {"lease_id": "diagnostic-only", "expires_at_ns": time.monotonic_ns() + 30_000_000_000},
                "terminal": {"release_all_required": True},
                "ops": ops,
            }
            started = time.monotonic_ns()
            dispatch = session.dispatch(program, current_observation_seq=7, current_binding_revision=3)
            ended = time.monotonic_ns()
            immediate_effect = effect.read_text(encoding="utf-8") if effect.exists() else None
            immediate_events = events.read_text(encoding="utf-8") if events.exists() else ""
            final_effect = effect.read_text(encoding="utf-8") if effect.exists() else None
            final_events = events.read_text(encoding="utf-8") if events.exists() else ""
            return {
                "case": case, "layout": "us", "dispatch_status": dispatch.get("status"),
                "dispatch_started_ns": started, "dispatch_ended_ns": ended,
                "completed_ops": dispatch.get("execution", {}).get("completed_ops"),
                "release_verified": dispatch.get("execution", {}).get("releases", [{}])[-1].get("verified"),
                "immediate_effect": immediate_effect, "final_effect": final_effect,
                "immediate_events": immediate_events, "final_events": final_events,
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
    cases = [run_case(False), run_case(True)]
    result = {"scope": "nonformal local Docker diagnostic; no XKB remap and no formal allocation", "cases": cases}
    output = Path(__file__).with_name("results") / "diagnostic02" / "raw.json"
    output.parent.mkdir(parents=True, exist_ok=False)
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result_path": str(output), "cases": [
        {key: case[key] for key in ("case", "dispatch_status", "completed_ops", "release_verified", "immediate_effect", "final_effect")}
        for case in cases
    ]}, sort_keys=True))
