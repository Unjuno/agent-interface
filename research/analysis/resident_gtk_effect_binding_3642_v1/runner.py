"""One immutable GTK/X11 effect-binding allocation for Issue #3642."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from Xlib import X, Xatom, display
from Xlib.ext import xtest


ROOT = Path("/src")
OUT = Path("/evidence")
POLICY_DIR = ROOT / "research/analysis/resident_gtk_sequence_guard_3588_v1"
FIXTURE = ROOT / "research/analysis/resident_gtk_effect_binding_3642_v1/fixture.py"
EVENTS = [
    {"kind": "obs", "id": "valid-gen1", "gen": 1, "seq": 1, "target": 1, "value": True},
    {"kind": "replace", "id": "replace-gen2", "gen": 2, "seq": 3, "target": 2},
    {"kind": "replace", "id": "delayed-replace-gen1", "gen": 1, "seq": 2, "target": 1},
    {"kind": "obs", "id": "stale-gen1", "gen": 1, "seq": 4, "target": 1, "value": True},
    {"kind": "obs", "id": "valid-gen2", "gen": 2, "seq": 5, "target": 2, "value": True},
]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def proc_start(pid: int) -> str | None:
    try:
        return Path(f"/proc/{pid}/stat").read_text().split()[21]
    except FileNotFoundError:
        return None


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load frozen module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def find_window(conn, prefix: str, timeout: float = 8.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        for window in conn.screen().root.query_tree().children:
            try:
                if (window.get_wm_name() or "").startswith(prefix):
                    return window
            except Exception:
                pass
        time.sleep(0.02)
    raise TimeoutError("GTK fixture window not found")


def read_frame(window, conn) -> tuple[int, int, bytes]:
    geometry = window.get_geometry()
    conn.sync()
    image = window.get_image(0, 0, geometry.width, geometry.height, X.ZPixmap, 0xFFFFFFFF)
    if image is None or not image.data:
        raise RuntimeError("XGetImage returned empty frame")
    return geometry.width, geometry.height, image.data


def wait_for_stable_frame(window, conn, expected_title: str, timeout: float = 3.0):
    deadline = time.monotonic() + timeout
    previous = None
    stable = 0
    latest = (0, 0, b"")
    while time.monotonic() < deadline:
        title = window.get_wm_name()
        latest = read_frame(window, conn)
        if title == expected_title and latest[2] == previous:
            stable += 1
        elif title == expected_title:
            stable = 0
        else:
            stable = 0
        previous = latest[2]
        if title == expected_title and stable >= 3:
            return latest
        time.sleep(0.03)
    raise TimeoutError(f"GTK title/frame did not stabilize at {expected_title!r}")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    allocation = {
        "schema": "issue-3642/gtk-effect-allocation-v1",
        "allocation_id": os.environ.get("ALLOCATION_ID"),
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "container_image_id": os.environ.get("OBSTAC_IMAGE_ID"),
        "container_platform": os.environ.get("OBSTAC_PLATFORM"),
        "display": ":201",
        "events": EVENTS,
        "prefixes": [],
        "key_releases": [],
    }
    xvfb = None
    app = None
    conn = None
    xvfb_log = (OUT / "xvfb.log").open("wb")
    app_log = None
    display_name = ":201"
    socket = Path("/tmp/.X11-unix/X201")
    started = time.monotonic_ns()
    try:
        xvfb = subprocess.Popen(
            ["/usr/bin/Xvfb", display_name, "-screen", "0", "640x480x24", "-nolisten", "tcp"],
            stdout=xvfb_log,
            stderr=subprocess.STDOUT,
        )
        allocation["xvfb_pid"] = xvfb.pid
        allocation["xvfb_start_ticks"] = proc_start(xvfb.pid)
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline and not socket.exists():
            if xvfb.poll() is not None:
                raise RuntimeError(f"Xvfb exited before socket readiness: {xvfb.returncode}")
            time.sleep(0.02)
        if not socket.exists():
            raise TimeoutError("Xvfb socket readiness timeout")

        conn = display.Display(display_name)
        window = None
        fixture_env = {**os.environ, "DISPLAY": display_name, "EFFECT_MODE": "on", "PYTHONDONTWRITEBYTECODE": "1"}
        app_log = (OUT / "fixture.log").open("wb")
        app = subprocess.Popen([sys.executable, "-B", str(FIXTURE)], cwd="/tmp", env=fixture_env,
                               stdin=subprocess.PIPE, stdout=app_log, stderr=subprocess.STDOUT, text=True)
        allocation["fixture_pid"] = app.pid
        allocation["fixture_start_ticks"] = proc_start(app.pid)
        window = find_window(conn, "resident-fixture:")
        deadline = time.monotonic() + 3
        while window.get_attributes().map_state != X.IsViewable and time.monotonic() < deadline:
            time.sleep(0.02)
        if window.get_attributes().map_state != X.IsViewable:
            raise RuntimeError("GTK fixture window is not viewable")
        # Focus using the server timestamp generated by this property change,
        # rather than CurrentTime (timestamp zero, which means "latest").
        window.change_attributes(event_mask=X.PropertyChangeMask)
        window.change_property(conn.intern_atom("_ISSUE_3642_SERVER_TIME"), Xatom.STRING,
                               8, b"timestamp")
        conn.sync()
        focus_time = None
        deadline = time.monotonic() + 2
        while focus_time is None and time.monotonic() < deadline:
            if conn.pending_events():
                ev = conn.next_event()
                if ev.type == X.PropertyNotify:
                    focus_time = ev.time
            else:
                time.sleep(0.01)
        if focus_time is None:
            raise RuntimeError("no server timestamp available for focus request")
        window.set_input_focus(X.RevertToParent, focus_time)
        conn.sync()
        time.sleep(0.05)
        focus = conn.get_input_focus().focus
        if focus not in (window, window.id):
            raise RuntimeError(f"GTK focus did not bind to fixture: {focus}")
        allocation["window_id"] = window.id

        candidate = load_module("policy_guarded", POLICY_DIR / "policies_guarded.py").Resident()
        oracle_module = load_module("independent_prefix_oracle", POLICY_DIR / "oracle.py")
        oracle = oracle_module.PrefixOracle()
        initial = wait_for_stable_frame(window, conn, "resident-fixture:0")
        (OUT / "frame-00.raw").write_bytes(initial[2])
        allocation["initial"] = {"title": window.get_wm_name(), "counter": 0,
                                  "frame_path": "frame-00.raw", "width": initial[0],
                                  "height": initial[1], "bytes": len(initial[2]),
                                  "sha256": sha(initial[2])}

        count = 0
        keycode = conn.keysym_to_keycode(0x20)
        for index, event in enumerate(EVENTS, start=1):
            before_candidate = len(candidate.actions)
            before_oracle = len(oracle.actions)
            candidate.step(event)
            oracle.consume(event)
            candidate_delta = [list(x) for x in candidate.actions[before_candidate:]]
            oracle_delta = [list(x) for x in oracle.actions[before_oracle:]]
            emitted = len(candidate_delta) == 1 and candidate_delta[0][0] == "emit"
            release_row = None
            if emitted:
                xtest.fake_input(conn, X.KeyPress, keycode)
                conn.sync()
                xtest.fake_input(conn, X.KeyRelease, keycode)
                conn.sync()
                keymap = conn.query_keymap()
                down = bool(keymap[keycode // 8] & (1 << (keycode % 8)))
                release_row = {"event_id": event["id"], "key": "Space", "keycode": keycode,
                               "verified_empty": not down, "keys_down": ["Space"] if down else []}
                allocation["key_releases"].append(release_row)
                if down:
                    raise RuntimeError("X11 physical Space release did not verify empty")
                count += 1
            expected_title = f"resident-fixture:{count}"
            if emitted:
                frame = wait_for_stable_frame(window, conn, expected_title)
            else:
                time.sleep(0.10)
                frame = read_frame(window, conn)
                if window.get_wm_name() != expected_title:
                    raise RuntimeError(f"unexpected GUI effect after non-emit {event['id']}")
            path = f"frame-{index:02d}.raw"
            (OUT / path).write_bytes(frame[2])
            allocation["prefixes"].append({
                "index": index,
                "event": event,
                "candidate_delta": candidate_delta,
                "oracle_delta": oracle_delta,
                "candidate_state": oracle_module.snapshot(candidate),
                "oracle_state": oracle_module.snapshot(oracle),
                "state_equal": oracle_module.snapshot(candidate) == oracle_module.snapshot(oracle),
                "emitted": emitted,
                "effect_count": count,
                "title": window.get_wm_name(),
                "frame_path": path,
                "width": frame[0],
                "height": frame[1],
                "bytes": len(frame[2]),
                "sha256": sha(frame[2]),
                "key_release": release_row,
            })

        allocation["final_effect_count"] = count
        allocation["candidate_state"] = oracle_module.snapshot(candidate)
        allocation["oracle_state"] = oracle_module.snapshot(oracle)
        allocation["status"] = "RUN_COMPLETED"
    except BaseException as exc:
        allocation["status"] = "STOP_OR_FAIL_RUNNER"
        allocation["runner_error"] = repr(exc)
        raise
    finally:
        allocation["ended_monotonic_ns"] = time.monotonic_ns()
        allocation["duration_ns"] = allocation["ended_monotonic_ns"] - started
        if conn is not None:
            conn.close()
        if app is not None and app.poll() is None:
            try:
                app.stdin.write("STOP\n")
                app.stdin.flush()
                app.stdin.close()
                app.wait(timeout=4)
            except (BrokenPipeError, subprocess.TimeoutExpired):
                if app.poll() is None:
                    app.terminate()
        if app is not None:
            try:
                app.wait(timeout=4)
            except subprocess.TimeoutExpired:
                app.kill()
                app.wait(timeout=4)
        allocation["fixture_exit_code"] = None if app is None else app.returncode
        allocation["fixture_reaped"] = app is None or app.poll() is not None
        if xvfb is not None and xvfb.poll() is None:
            xvfb.terminate()
        if xvfb is not None:
            try:
                xvfb.wait(timeout=4)
            except subprocess.TimeoutExpired:
                xvfb.kill()
                xvfb.wait(timeout=4)
        allocation["xvfb_exit_code"] = None if xvfb is None else xvfb.returncode
        allocation["xvfb_reaped"] = xvfb is None or xvfb.poll() is not None
        allocation["x11_socket_removed"] = not socket.exists()
        allocation["xvfb_log_sha256"] = sha((OUT / "xvfb.log").read_bytes()) if (OUT / "xvfb.log").exists() else None
        allocation["fixture_log_sha256"] = sha((OUT / "fixture.log").read_bytes()) if (OUT / "fixture.log").exists() else None
        if app_log is not None:
            app_log.close()
        xvfb_log.close()
        (OUT / "allocation.json").write_text(json.dumps(allocation, indent=2, sort_keys=True) + "\n")
    return 0 if allocation.get("status") == "RUN_COMPLETED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
