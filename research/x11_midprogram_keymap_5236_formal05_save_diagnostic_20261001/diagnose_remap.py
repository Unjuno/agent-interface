"""Nonformal Docker diagnostic of save-chord events after mid-program XKB remaps."""
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

ROWS = (("control_us", "us", None), ("jp_to_us", "jp", "us"), ("us_to_jp", "us", "jp"))


def run_row(row: str, initial: str, target: str | None) -> dict:
    with tempfile.TemporaryDirectory(prefix="issue5236-remap-diag-") as temp:
        root = Path(temp)
        log = (root / "xvfb.log").open("wb")
        server = subprocess.Popen(
            ["Xvfb", "-displayfd", "1", "-screen", "0", "1024x768x24", "-nolisten", "tcp", "-noreset"],
            stdout=subprocess.PIPE, stderr=log, text=True, bufsize=1,
        )
        fixture = backend = anchor = actor = None
        try:
            ready, _, _ = select.select([server.stdout], [], [], 8)
            display = ":" + server.stdout.readline().strip() if ready else ""
            if not display[1:].isdecimal():
                raise RuntimeError("Xvfb did not report a display")
            anchor = Display(display)
            setup = subprocess.run(["setxkbmap", "-display", display, "-layout", initial], capture_output=True, text=True)
            if setup.returncode:
                raise RuntimeError("initial setxkbmap failed: " + setup.stderr)
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
            actor_code = (
                "import json,subprocess,sys,time; d,t,out=sys.argv[1:]; time.sleep(.25); "
                "start=time.monotonic_ns(); p=subprocess.run(['setxkbmap','-display',d,'-layout',t],capture_output=True,text=True); "
                "end=time.monotonic_ns(); open(out,'w').write(json.dumps({'started_ns':start,'ended_ns':end,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr})); sys.exit(p.returncode)"
            )
            actor_path = root / "actor.json"
            if target:
                actor = subprocess.Popen([sys.executable, "-c", actor_code, display, target, str(actor_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            program = {
                "schema": "agent-interface/program-v1",
                "program_id": "issue5236-docker-remap-diag-" + row,
                "source": {"observation_seq": 7, "binding_revision": 3},
                "authority": {"lease_id": "diagnostic-only", "expires_at_ns": time.monotonic_ns() + 30_000_000_000},
                "terminal": {"release_all_required": True},
                "ops": [
                    {"op": "focus", "target": "fixture"},
                    {"op": "pointer_move", "target": "fixture", "frame": "window_client", "x": 50, "y": 55},
                    {"op": "pointer_button", "button": "left", "down": True},
                    {"op": "pointer_button", "button": "left", "down": False},
                    {"op": "text", "text": "a"},
                    {"op": "wait_update", "timeout_ms": 1500},
                    {"op": "text", "text": "_"},
                    {"op": "key_chord", "keys": ["CTRL", "S"]},
                    {"op": "release_all"},
                ],
            }
            started = time.monotonic_ns()
            dispatch = session.dispatch(program, current_observation_seq=7, current_binding_revision=3)
            ended = time.monotonic_ns()
            actor_out, actor_err = actor.communicate(timeout=8) if actor else ("", "")
            final_layout = subprocess.run(["setxkbmap", "-display", display, "-query"], capture_output=True, text=True)
            return {
                "row": row, "initial": initial, "target": target, "layout_after": final_layout.stdout,
                "dispatch_status": dispatch.get("status"), "completed_ops": dispatch.get("execution", {}).get("completed_ops"),
                "release_verified": dispatch.get("execution", {}).get("releases", [{}])[-1].get("verified"),
                "started_ns": started, "ended_ns": ended, "actor": json.loads(actor_path.read_text()) if actor_path.exists() else None,
                "actor_exit": actor.returncode if actor else None, "actor_stdout": actor_out, "actor_stderr": actor_err,
                "saved_effect": effect.read_text(encoding="utf-8") if effect.exists() else None,
                "events": events.read_text(encoding="utf-8") if events.exists() else "",
                "setup_stdout": setup.stdout, "setup_stderr": setup.stderr,
            }
        finally:
            if backend is not None:
                backend.close()
            if actor is not None and actor.poll() is None:
                actor.terminate()
                actor.wait(timeout=3)
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
    rows = [run_row(*spec) for spec in ROWS]
    result = {"scope": "nonformal Docker remap diagnostic; no formal allocation or Arch result", "rows": rows}
    output = Path(__file__).with_name("results") / "diagnostic03" / "raw.json"
    output.parent.mkdir(parents=True, exist_ok=False)
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result_path": str(output), "rows": [
        {key: row[key] for key in ("row", "layout_after", "dispatch_status", "completed_ops", "release_verified", "actor_exit", "saved_effect")}
        for row in rows
    ]}, sort_keys=True))
