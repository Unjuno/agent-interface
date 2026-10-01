"""One-shot private-Xvfb runner for Issue #5236; no retries or row repair."""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path
import Xlib

from runtime.backends.x11_v1.backend import X11Backend
from runtime.backends.x11_v1.session import X11RuntimeSession
from runtime.core_v1.contract import SCHEMA_PROGRAM

ROWS = (
    ("control_us", "us", None),
    ("jp_to_us", "jp", "us"),
    ("us_to_jp", "us", "jp"),
)
WAIT_MS = 1500
TEXT_BEFORE = "a"
TEXT_AFTER = "_"
EXPECTED = TEXT_BEFORE + TEXT_AFTER


def run_row(root: Path, display_name: str, row_id: str, initial: str, target: str | None) -> dict:
    row_dir = root / row_id
    row_dir.mkdir()
    meta, effect, events = (row_dir / name for name in ("meta.json", "effect.json", "events.jsonl"))
    layout = subprocess.run(
        ["setxkbmap", "-display", display_name, "-layout", initial],
        text=True, capture_output=True, check=False,
    )
    record = {"row": row_id, "initial_layout": initial, "target_layout": target,
              "layout_setup_argv": ["setxkbmap", "-display", display_name, "-layout", initial],
              "layout_setup_exit": layout.returncode, "layout_setup_stdout": layout.stdout,
              "layout_setup_stderr": layout.stderr}
    if layout.returncode:
        return record | {"status": "STOP_LAYOUT_SETUP"}
    layout_initial = subprocess.run(["setxkbmap", "-display", display_name, "-query"],
                                    text=True, capture_output=True, check=False)
    record["layout_initial_argv"] = ["setxkbmap", "-display", display_name, "-query"]
    record["layout_initial_exit"] = layout_initial.returncode
    record["layout_initial_stdout"] = layout_initial.stdout
    record["layout_initial_stderr"] = layout_initial.stderr
    if layout_initial.returncode:
        return record | {"status": "STOP_LAYOUT_READBACK"}
    fixture = subprocess.Popen(
        [sys.executable, "-m", "runtime.backends.x11_v1.fixture_app", "--meta", str(meta),
         "--effect", str(effect), "--events", str(events)],
        env=os.environ | {"DISPLAY": display_name}, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True,
    )
    actor = None
    backend = None
    try:
        deadline = time.monotonic() + 8
        while not meta.exists() and time.monotonic() < deadline:
            if fixture.poll() is not None:
                return record | {"status": "STOP_FIXTURE_EXIT", "fixture_exit": fixture.returncode}
            time.sleep(0.02)
        if not meta.exists():
            return record | {"status": "STOP_FIXTURE_TIMEOUT"}
        wid = json.loads(meta.read_text(encoding="utf-8"))["window_id"]
        backend = X11Backend(display_name, {"fixture": wid})
        session = X11RuntimeSession(backend)
        actor_spec = None
        if target:
            actor_code = (
                "import json,subprocess,sys,time; "
                "d,t,out=sys.argv[1:]; time.sleep(0.25); start=time.monotonic_ns(); "
                "p=subprocess.run(['setxkbmap','-display',d,'-layout',t],capture_output=True,text=True); "
                "end=time.monotonic_ns(); "
                "open(out,'w').write(json.dumps({'argv':['setxkbmap','-display',d,'-layout',t],"
                "'target_layout':t,'started_ns':start,'ended_ns':end,'exit':p.returncode,"
                "'stdout':p.stdout,'stderr':p.stderr},sort_keys=True)+'\\n'); sys.exit(p.returncode)"
            )
            actor = subprocess.Popen([sys.executable, "-c", actor_code, display_name, target,
                                      str(row_dir / "actor.json")],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            actor_spec = [sys.executable, "-c", actor_code, display_name, target,
                          str(row_dir / "actor.json")]
        program = {
            "schema": SCHEMA_PROGRAM, "program_id": "issue5236-" + row_id,
            "source": {"observation_seq": 7, "binding_revision": 3},
            "authority": {"lease_id": "issue5236-local-xvfb", "expires_at_ns": time.monotonic_ns() + 30_000_000_000},
            "terminal": {"release_all_required": True},
            "ops": [
                {"op": "focus", "target": "fixture"},
                {"op": "text", "text": TEXT_BEFORE},
                {"op": "wait_update", "timeout_ms": WAIT_MS},
                {"op": "text", "text": TEXT_AFTER},
                {"op": "key_chord", "keys": ["CTRL", "S"]},
                {"op": "release_all"},
            ],
        }
        dispatch_started = time.monotonic_ns()
        receipt = session.dispatch(program, current_observation_seq=7, current_binding_revision=3)
        dispatch_ended = time.monotonic_ns()
        actor_out, actor_err = actor.communicate(timeout=8) if actor else ("", "")
        fixture_out, fixture_err = fixture.communicate(timeout=2) if fixture.poll() is not None else ("", "")
        observed = effect.read_bytes().hex() if effect.exists() else None
        layout_after = subprocess.run(["setxkbmap", "-display", display_name, "-query"],
                                      text=True, capture_output=True, check=False)
        actor_receipt = json.loads((row_dir / "actor.json").read_text(encoding="utf-8")) if actor and (row_dir / "actor.json").exists() else None
        event_hex = events.read_bytes().hex() if events.exists() else None
        backend.close()
        backend = None
        fixture.terminate()
        fixture.wait(timeout=3)
        fixture_out, fixture_err = fixture.communicate()
        record |= {
            "status": "row_complete", "program": program, "dispatch_started_ns": dispatch_started,
            "dispatch_ended_ns": dispatch_ended, "receipt": receipt,
            "saved_effect_hex": observed, "expected_effect_hex": (json.dumps(
                {"saved": True, "text": EXPECTED}, sort_keys=True) + "\n").encode().hex(),
            "layout_after_argv": ["setxkbmap", "-display", display_name, "-query"],
            "layout_after_exit": layout_after.returncode, "layout_after_stdout": layout_after.stdout,
            "layout_after_stderr": layout_after.stderr,
            "events_hex": event_hex,
            "actor_argv": actor_spec, "actor_exit": actor.returncode if actor else None,
            "actor_target": target, "actor_receipt": actor_receipt,
            "actor_stdout": actor_out, "actor_stderr": actor_err,
            "fixture_exit": fixture.returncode, "fixture_terminated_for_cleanup": fixture.returncode == -15,
            "fixture_stdout": fixture_out, "fixture_stderr": fixture_err,
        }
        return record
    finally:
        if backend is not None:
            backend.close()
        if actor is not None and actor.poll() is None:
            actor.terminate()
            actor.wait(timeout=3)
        if fixture.poll() is None:
            fixture.terminate()
            try:
                fixture.wait(timeout=3)
            except subprocess.TimeoutExpired:
                fixture.kill()
                fixture.wait()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        raise SystemExit("STOP_OUTPUT_COLLISION")
    args.output.mkdir(parents=True)
    server_start_ns = time.monotonic_ns()
    server = subprocess.Popen(["Xvfb", "-displayfd", "1", "-screen", "0", "1024x768x24",
                               "-nolisten", "tcp", "-noreset", "-ac"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    raw = {"rows": [], "xvfb": {"argv": ["Xvfb", "-displayfd", "1", "-screen", "0", "1024x768x24", "-nolisten", "tcp", "-noreset", "-ac"],
                                  "pid": server.pid, "started_ns": server_start_ns},
           "environment": {"python": sys.version, "platform": platform.platform(),
                           "python_xlib": getattr(Xlib, "__version__", "unknown"),
                           "display_server": "private Xvfb", "network": "not used by runner",
                           "model_gpu_docker": False}}
    try:
        display_number = server.stdout.readline().strip()
        if not display_number.isdecimal():
            raw["stop"] = "STOP_XVFB_STARTUP"
            raw["xvfb"]["displayfd_stdout"] = display_number
            return 2
        display_name = ":" + display_number
        results = []
        for row_id, initial, target in ROWS:
            results.append(run_row(args.output, display_name, row_id, initial, target))
            if results[-1]["status"] != "row_complete":
                break
        raw["rows"] = results
        raw["display"] = display_name
        raw["xvfb"]["display"] = display_name
        return 0 if len(results) == len(ROWS) and all(r["status"] == "row_complete" for r in results) else 2
    finally:
        stop_started_ns = time.monotonic_ns()
        server.terminate()
        try:
            server.wait(timeout=3)
            cleanup_action = "terminate"
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()
            cleanup_action = "kill_after_timeout"
        raw["xvfb"].update(stop_started_ns=stop_started_ns, ended_ns=time.monotonic_ns(),
                           exit=server.returncode, cleanup_action=cleanup_action,
                           stderr=server.stderr.read())
        (args.output / "raw.json").write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
