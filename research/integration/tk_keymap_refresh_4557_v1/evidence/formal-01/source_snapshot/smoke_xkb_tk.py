#!/usr/bin/env python3
"""Excluded one-session Docker construction probe; never formal evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import signal
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

from Xlib import X, XK, display, xauth
from Xlib.ext import xtest
from Xlib.support import unix_connect


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def wait_until(predicate, description: str, timeout: float = 5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(0.01)
    raise TimeoutError(f"timeout waiting for {description}")


def server_keymap(keycode: int) -> dict[str, object]:
    connection = display.Display()
    try:
        values = connection.get_keyboard_mapping(keycode, 1)[0]
        names = [XK.keysym_to_string(value) for value in values]
        return {"keycode": keycode, "keysyms": names}
    finally:
        connection.close()


def send_chord(window_id: int, keycode: int, phase: str) -> dict[str, object]:
    connection = display.Display()
    observer = display.Display()
    try:
        window = connection.create_resource_object("window", window_id)
        connection.set_input_focus(window, X.RevertToParent, X.CurrentTime)
        connection.sync()
        actual_focus = connection.get_input_focus().focus
        if getattr(actual_focus, "id", actual_focus) != window_id:
            raise RuntimeError(f"focus owner mismatch for {phase}: {actual_focus!r}")
        xtest.fake_input(connection, X.KeyPress, detail=keycode)
        connection.sync()
        press_keymap = observer.query_keymap()
        press_down = bool(press_keymap[keycode // 8] & (1 << (keycode % 8)))
        xtest.fake_input(connection, X.KeyRelease, detail=keycode)
        connection.sync()
        release_keymap = observer.query_keymap()
        release_down = bool(release_keymap[keycode // 8] & (1 << (keycode % 8)))
        return {"phase": phase, "target_window_id": window_id,
                "request_sequence": [{"type": "KeyPress", "detail": keycode},
                                     {"type": "KeyRelease", "detail": keycode}],
                "observer_states": {"after_press": press_down, "after_release": release_down},
                "sent_monotonic_ns": time.monotonic_ns(), "terminal_key_down": release_down}
    finally:
        observer.close()
        connection.close()


def start_fixture(label: str, directory: Path, fixture: Path, env: dict[str, str], child_logs):
    events = directory / f"{label}.events.jsonl"
    ready = directory / f"{label}.ready.jsonl"
    phase_file = directory / f"{label}.phase"
    phase_file.write_text("BOOT\n", encoding="ascii")
    stdout = (directory / f"{label}.stdout.txt").open("w", encoding="utf-8")
    stderr = (directory / f"{label}.stderr.txt").open("w", encoding="utf-8")
    child_logs.extend([stdout, stderr])
    process = subprocess.Popen(
        [sys.executable, str(fixture), "--label", label, "--events", str(events),
         "--ready", str(ready), "--phase-file", str(phase_file)],
        env=env,
        stdout=stdout,
        stderr=stderr,
    )
    record = wait_until(lambda: read_jsonl(ready)[0] if read_jsonl(ready) else None, f"{label} Tk ready")
    if record.get("pid") != process.pid:
        raise RuntimeError(f"{label} readiness PID mismatch")
    return process, events, record, phase_file


def collect_pair(path: Path, before: int) -> list[dict[str, object]]:
    return wait_until(lambda: (rows if len(rows := read_jsonl(path)) >= before + 2 else None), f"two Tk events in {path.name}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--fixture", type=Path, default=Path(__file__).with_name("tk_fixture.py"))
    parser.add_argument("--allocation-id", default="tk-xkb-refresh-4557-construction-excluded-01")
    parser.add_argument("--formal", action="store_true")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    snapshot_dir = args.out / "source_snapshot"
    snapshot_dir.mkdir()
    for source in Path(__file__).parent.iterdir():
        if source.is_file() and (source.suffix == ".py" or source.name == "Dockerfile"):
            shutil.copyfile(source, snapshot_dir / source.name)

    display_name = ":99"
    authority = Path("/tmp") / f"xauthority-{secrets.token_hex(6)}"
    cookie = secrets.token_hex(16)
    env = os.environ.copy()
    env.update({"DISPLAY": display_name, "XAUTHORITY": str(authority), "HOME": "/tmp", "LANG": "C.UTF-8"})
    # Python-Xlib reads XAUTHORITY from this process environment, not the env
    # mapping passed later to Xvfb/setxkbmap/Tk children.
    os.environ.update({key: env[key] for key in ("DISPLAY", "XAUTHORITY", "HOME", "LANG")})
    xauth_add = subprocess.run(
        ["xauth", "-f", str(authority), "add", display_name, ".", cookie],
        text=True, capture_output=True, env=env, check=False,
    )
    if xauth_add.returncode != 0:
        raise RuntimeError(f"xauth failed: {xauth_add.stderr}")

    xvfb_log = args.out / "xvfb.stderr.txt"
    xvfb_stream = xvfb_log.open("w", encoding="utf-8")
    server = subprocess.Popen(
        ["Xvfb", display_name, "-screen", "0", "800x600x24", "-nolisten", "tcp", "-auth", str(authority)],
        stdout=subprocess.DEVNULL, stderr=xvfb_stream, env=env,
    )
    fixtures: list[subprocess.Popen] = []
    child_logs = []
    display_errors: list[str] = []
    summary: dict[str, object] = {
        "allocation_id": args.allocation_id,
        "formal": args.formal,
        "source_paths": {
            source.name: f"/repo/research/integration/tk_keymap_refresh_4557_v1/{source.name}"
            for source in snapshot_dir.iterdir()
        },
        "display": display_name,
        "source_sha256": {source.name: sha256(source) for source in snapshot_dir.iterdir()},
        "xvfb_pid": server.pid,
        "xvfb_command": ["Xvfb", display_name, "-screen", "0", "800x600x24",
                         "-nolisten", "tcp", "-auth", str(authority)],
        "xauthority_sha256": hashlib.sha256(authority.read_bytes()).hexdigest(),
        "steps": [],
    }
    failed = False
    result_code = 0
    try:
        xauth_readback = subprocess.run(
            ["xauth", "-f", str(authority), "list"], text=True, capture_output=True,
            env=env, check=False,
        )
        sanitized_xauth = "\n".join(
            " ".join(line.split()[:-1] + ["[COOKIE REDACTED]"])
            for line in xauth_readback.stdout.splitlines()
        )
        (args.out / "xauth.list.txt").write_text(sanitized_xauth + "\n", encoding="utf-8")
        (args.out / "xauth.stderr.txt").write_text(xauth_readback.stderr, encoding="utf-8")
        if xauth_readback.returncode != 0:
            raise RuntimeError(f"xauth readback failed: {xauth_readback.stderr}")
        wait_until(lambda: _display_ready(env, display_errors), "authenticated Xvfb")
        us = subprocess.run(["setxkbmap", "-display", display_name, "-layout", "us"], text=True, capture_output=True, env=env, check=False)
        if us.returncode != 0:
            raise RuntimeError(f"setxkbmap us failed: {us.stderr}")
        keycode = 29
        us_map = server_keymap(keycode)

        old_proc, old_events, old_ready, old_phase = start_fixture("old", args.out, args.fixture, env, child_logs)
        fixtures.append(old_proc)
        baseline_before = len(read_jsonl(old_events))
        old_phase.write_text("us_baseline\n", encoding="ascii")
        baseline_send = send_chord(int(old_ready["window_id"]), keycode, "us_baseline")
        baseline_rows = wait_until(lambda: (rows if len(rows := read_jsonl(old_events)) >= baseline_before + 2 else None), "US baseline events")
        baseline = baseline_rows[baseline_before:baseline_before + 2]
        _assert_pair(baseline, "us_baseline", keycode, "y")

        de = subprocess.run(["setxkbmap", "-display", display_name, "-layout", "de"], text=True, capture_output=True, env=env, check=False)
        if de.returncode != 0:
            raise RuntimeError(f"setxkbmap de failed: {de.stderr}")
        de_map = _wait_for_map(keycode, "z")
        old_phase.write_text("existing_after_de\n", encoding="ascii")
        old_before = len(read_jsonl(old_events))
        old_send = send_chord(int(old_ready["window_id"]), keycode, "existing_after_de")
        old_rows = wait_until(lambda: (rows if len(rows := read_jsonl(old_events)) >= old_before + 2 else None), "existing Tk events after layout change")
        old_after = old_rows[old_before:old_before + 2]
        _assert_pair(old_after, "existing_after_de", keycode, None)

        fresh_proc, fresh_events, fresh_ready, fresh_phase = start_fixture("fresh", args.out, args.fixture, env, child_logs)
        fixtures.append(fresh_proc)
        fresh_before = len(read_jsonl(fresh_events))
        fresh_phase.write_text("fresh_after_de\n", encoding="ascii")
        fresh_send = send_chord(int(fresh_ready["window_id"]), keycode, "fresh_after_de")
        fresh_rows = wait_until(lambda: (rows if len(rows := read_jsonl(fresh_events)) >= fresh_before + 2 else None), "fresh Tk events after layout change")
        fresh_after = fresh_rows[fresh_before:fresh_before + 2]
        _assert_pair(fresh_after, "fresh_after_de", keycode, "z")

        summary["steps"] = [
            {"phase": "us_baseline", "server_map": us_map, "send": baseline_send,
             "window_id": old_ready["window_id"], "events": baseline},
            {"phase": "existing_after_de", "server_map": de_map, "send": old_send,
             "window_id": old_ready["window_id"], "events": old_after},
            {"phase": "fresh_after_de", "server_map": server_keymap(keycode), "send": fresh_send,
             "window_id": fresh_ready["window_id"], "events": fresh_after},
        ]
        summary["disposition"] = "FORMAL_SESSION_COMPLETE" if args.formal else "CONSTRUCTION_MECHANICS_ONLY"
    except Exception as exc:
        failed = True
        result_code = 1
        summary["error"] = f"{type(exc).__name__}: {exc}"
        summary["partial_steps"] = read_jsonl(args.out / "old.events.jsonl")
        summary["xvfb_returncode_at_error"] = server.poll()
        summary["display_probe_errors"] = display_errors[-10:]
        summary["xauthority_sha256"] = hashlib.sha256(authority.read_bytes()).hexdigest() if authority.exists() else None
        summary["xauth_diagnostics"] = _xauth_diagnostics(display_name, authority, env)
    finally:
        for process in reversed(fixtures):
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
            (args.out / f"child-{process.pid}.exit.json").write_text(
                json.dumps({"pid": process.pid, "returncode": process.returncode}, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        if server.poll() is None:
            server.send_signal(signal.SIGTERM)
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=2)
        xvfb_stream.close()
        summary["xvfb_exit_code"] = server.poll()
        (args.out / "xvfb.exit.json").write_text(
            json.dumps({"pid": server.pid, "returncode": server.returncode}, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        authority.unlink(missing_ok=True)
        for stream in child_logs:
            stream.close()
        summary["child_exit_codes"] = {str(process.pid): process.returncode for process in fixtures}
        summary["xvfb_exit_code"] = server.returncode
        output_name = "construction.partial.json" if failed else "summary.json"
        (args.out / output_name).write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(json.dumps(summary, sort_keys=True))
    return result_code


def _display_ready(env: dict[str, str], errors: list[str] | None = None) -> bool:
    try:
        connection = display.Display(env["DISPLAY"])
    except Exception as exc:
        if errors is not None:
            errors.append(f"{type(exc).__name__}: {exc}")
        return False
    connection.close()
    return True


def _xauth_diagnostics(display_name: str, authority: Path, env: dict[str, str]) -> dict[str, object]:
    result: dict[str, object] = {
        "hostname": socket.gethostname(),
        "display": display_name,
        "xauthority_env": env.get("XAUTHORITY"),
        "home": env.get("HOME"),
        "file_exists": authority.is_file(),
    }
    if authority.is_file():
        stat = authority.stat()
        result["file_stat"] = {"mode": oct(stat.st_mode & 0o777), "uid": stat.st_uid,
                               "gid": stat.st_gid, "size": stat.st_size}
        records = xauth.Xauthority(str(authority))
        result["records"] = [
            {"family": family, "address": address.decode("utf-8", "replace"),
             "display_number": number.decode("ascii", "replace"),
             "protocol": protocol.decode("ascii", "replace")}
            for family, address, number, protocol, _cookie in records.entries
        ]
    try:
        _name, protocol, host, display_number, _screen = unix_connect.get_display(display_name)
        sock = unix_connect.get_socket(display_name, protocol, host, display_number)
        try:
            auth_name, auth_data = unix_connect.new_get_auth(sock, display_name, protocol, host, display_number)
            result["python_xlib_auth_selection"] = {
                "protocol": auth_name.decode("ascii", "replace"),
                "data_length": len(auth_data),
                "selected": bool(auth_data),
            }
        finally:
            sock.close()
    except Exception as exc:
        result["python_xlib_auth_selection_error"] = f"{type(exc).__name__}: {exc}"
    return result


def _wait_for_map(keycode: int, expected: str) -> dict[str, object]:
    def matches():
        current = server_keymap(keycode)
        return current if expected in current["keysyms"] else None

    return wait_until(matches, f"server map keycode {keycode} -> {expected}")


def _assert_pair(rows: list[dict[str, object]], phase: str, keycode: int, expected: str | None) -> None:
    if len(rows) != 2:
        raise RuntimeError(f"{phase}: expected exactly two events, got {len(rows)}")
    if [row.get("kind") for row in rows] != ["press", "release"]:
        raise RuntimeError(f"{phase}: press/release mismatch: {rows!r}")
    for row in rows:
        if row.get("phase") != phase or row.get("keycode") != keycode:
            raise RuntimeError(f"{phase}: wrong phase/keycode event: {row!r}")
        if expected is not None and row.get("keysym") != expected:
            raise RuntimeError(f"{phase}: expected {expected}, got {row.get('keysym')!r}")


if __name__ == "__main__":
    raise SystemExit(main())
