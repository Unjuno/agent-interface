#!/usr/bin/env python3
"""One-pair construction pilot for Issue #4448; not the formal allocation."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import traceback

from Xlib import X, XK, display
from Xlib.ext import xtest


def now() -> int:
    return time.monotonic_ns()


def child(effect_path: Path, ready_path: Path, arm: str, count: int) -> int:
    ready_path.write_text(f"{os.getpid()}\n")
    sequence = 0
    while sequence < count:
        line = sys.stdin.buffer.readline()
        if not line:
            return 3
        receipt = {"arm": arm, "sequence": sequence, "pid": os.getpid()}
        fd = os.open(effect_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            os.write(fd, (json.dumps(receipt, sort_keys=True) + "\n").encode())
            os.fsync(fd)
        finally:
            os.close(fd)
        sequence += 1
    return 0


def descendants(window, title: str):
    try:
        name = window.get_wm_name()
        if name == title:
            yield window
        for child_window in window.query_tree().children:
            yield from descendants(child_window, title)
    except Exception:
        return


def wait_window(dpy, title: str, timeout_s: float = 8.0):
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        matches = list(descendants(dpy.screen().root, title))
        if matches:
            return matches[0]
        time.sleep(0.01)
    raise TimeoutError(f"xterm window not found: {title}")


def keymap_is_neutral(dpy) -> bool:
    return not any(dpy.query_keymap())


def run_arm(arm: str, pair_id: str, root: Path) -> dict:
    effect_dir = root / pair_id / arm
    effect_dir.mkdir(parents=True)
    effect_path = effect_dir / "effects.jsonl"
    env = os.environ.copy()
    env["DISPLAY"] = ":99"
    env["HOME"] = "/tmp/issue4448-home"
    env["XDG_CACHE_HOME"] = "/tmp/issue4448-cache"
    Path(env["HOME"]).mkdir(parents=True, exist_ok=True)
    Path(env["XDG_CACHE_HOME"]).mkdir(parents=True, exist_ok=True)
    start = now()
    processes: list[subprocess.Popen] = []
    actions = []
    serial = 0
    xterm_pid_set: list[int] = []
    child_pid_set: list[int] = []
    log_handles = []
    try:
        if arm == "ephemeral":
            for serial in range(4):
                title = f"4448-{pair_id}-{arm}-{serial}"
                action_start = now()
                log_handle = (effect_dir / f"xterm-{serial}.log").open("wb")
                log_handles.append(log_handle)
                proc = subprocess.Popen([
                    "xterm", "-geometry", "80x24+0+0", "-title", title,
                    "-e", sys.executable, str(Path(__file__).resolve()), "--child",
                    "--effect", str(effect_path), "--ready", str(effect_dir / f"ready-{serial}"),
                    "--arm", arm, "--count", "1",
                ], env=env, stdout=log_handle, stderr=subprocess.STDOUT)
                processes.append(proc)
                xterm_pid_set.append(proc.pid)
                (effect_dir / f"launch-{serial}.json").write_text(json.dumps({
                    "argv": ["xterm", "-geometry", "80x24+0+0", "-title", title,
                             "-e", sys.executable, str(Path(__file__).resolve()), "--child",
                             "--effect", str(effect_path), "--ready",
                             str(effect_dir / f"ready-{serial}"), "--arm", arm,
                             "--count", "1"],
                    "xterm_pid": proc.pid,
                }, sort_keys=True) + "\n")
                dpy = display.Display()
                window = wait_window(dpy, title)
                try:
                    wait_ready(effect_dir / f"ready-{serial}")
                except TimeoutError as exc:
                    children_file = Path(f"/proc/{proc.pid}/task/{proc.pid}/children")
                    child_pids = children_file.read_text().strip() if children_file.exists() else "missing"
                    err_file = effect_dir / "child-exception.txt"
                    err = err_file.read_text() if err_file.exists() else "none"
                    raise TimeoutError(
                        f"{exc}; xterm_poll={proc.poll()}; child_pids={child_pids}; child_error={err}"
                    ) from exc
                window.set_input_focus(X.RevertToParent, X.CurrentTime)
                dpy.sync()
                keycode = dpy.keysym_to_keycode(XK.string_to_keysym("Return"))
                xtest.fake_input(dpy, X.KeyPress, detail=keycode)
                xtest.fake_input(dpy, X.KeyRelease, detail=keycode)
                dpy.sync()
                child_pid_set.append(wait_effect(effect_path, serial)["pid"])
                effect_seen = now()
                neutral = wait_neutral(dpy)
                exit_code = proc.wait(timeout=8)
                ready = now()
                actions.append({
                    "sequence": serial, "xterm_pid": proc.pid, "xterm_exit": exit_code,
                    "effect_observed_ns": effect_seen, "keymap_neutral_ns": neutral,
                    "next_ready_ns": ready, "keymap_neutral": True,
                    "effect_to_next_ready_ns": ready - effect_seen,
                    "action_start_ns": action_start,
                })
                dpy.close()
        else:
            title = f"4448-{pair_id}-{arm}-resident"
            log_handle = (effect_dir / "xterm-resident.log").open("wb")
            log_handles.append(log_handle)
            proc = subprocess.Popen([
                "xterm", "-geometry", "80x24+0+0", "-title", title,
                "-e", sys.executable, str(Path(__file__).resolve()), "--child",
                "--effect", str(effect_path), "--ready", str(effect_dir / "ready-resident"),
                "--arm", arm, "--count", "4",
            ], env=env, stdout=log_handle, stderr=subprocess.STDOUT)
            processes.append(proc)
            xterm_pid_set.append(proc.pid)
            dpy = display.Display()
            window = wait_window(dpy, title)
            wait_ready(effect_dir / "ready-resident")
            window.set_input_focus(X.RevertToParent, X.CurrentTime)
            dpy.sync()
            keycode = dpy.keysym_to_keycode(XK.string_to_keysym("Return"))
            for serial in range(4):
                action_start = now()
                xtest.fake_input(dpy, X.KeyPress, detail=keycode)
                xtest.fake_input(dpy, X.KeyRelease, detail=keycode)
                dpy.sync()
                record = wait_effect(effect_path, serial)
                child_pid_set.append(record["pid"])
                effect_seen = now()
                neutral = wait_neutral(dpy)
                ready = now()
                still_live = proc.poll() is None
                actions.append({
                    "sequence": serial, "xterm_pid": proc.pid, "child_pid": record["pid"],
                    "effect_observed_ns": effect_seen, "keymap_neutral_ns": neutral,
                    "next_ready_ns": ready, "keymap_neutral": True,
                    "effect_to_next_ready_ns": ready - effect_seen,
                    "action_start_ns": action_start,
                    "xterm_and_child_still_live": still_live,
                })
                if serial < 3 and not still_live:
                    raise RuntimeError("resident process exited before all four actions")
            final_effect = now()
            exit_code = proc.wait(timeout=8)
            shutdown_ns = now()
            for row in actions:
                row["xterm_exit"] = exit_code
                row["resident_final_shutdown_ns"] = shutdown_ns - final_effect
            dpy.close()
        end = now()
        records = [json.loads(x) for x in effect_path.read_text().splitlines()]
        return {
            "arm": arm, "pair_id": pair_id, "session_start_ns": start,
            "session_end_ns": end, "session_wall_ns": end - start,
            "actions": actions, "effect_records": records,
            "xterm_pids": xterm_pid_set, "child_pids": child_pid_set,
            "xterm_exits": [p.returncode for p in processes],
            "release_verified": all(x["keymap_neutral"] for x in actions),
        }
    finally:
        for proc in processes:
            if proc.poll() is None:
                proc.send_signal(signal.SIGTERM)
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
        for handle in log_handles:
            handle.close()


def wait_effect(path: Path, sequence: int, timeout_s: float = 5.0) -> dict:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if path.exists():
            rows = [json.loads(x) for x in path.read_text().splitlines()]
            if len(rows) > sequence:
                return rows[sequence]
        time.sleep(0.001)
    raise TimeoutError(f"effect row {sequence} missing")


def wait_ready(path: Path, timeout_s: float = 5.0) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if path.exists():
            return
        time.sleep(0.005)
    raise TimeoutError(f"child readiness receipt missing: {path.name}")


def wait_neutral(dpy, timeout_s: float = 2.0) -> int:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if keymap_is_neutral(dpy):
            return now()
        time.sleep(0.001)
    raise TimeoutError("XQueryKeymap did not return to neutral")


def start_display(log_dir: Path) -> list[subprocess.Popen]:
    env = os.environ.copy()
    env["HOME"] = "/tmp/issue4448-home"
    env["XDG_CACHE_HOME"] = "/tmp/issue4448-cache"
    Path(env["HOME"]).mkdir(parents=True, exist_ok=True)
    Path(env["XDG_CACHE_HOME"]).mkdir(parents=True, exist_ok=True)
    xvfb_log = (log_dir / "xvfb.log").open("wb")
    wm_log = (log_dir / "openbox.log").open("wb")
    xvfb = subprocess.Popen([
        "Xvfb", ":99", "-screen", "0", "1024x768x24", "+extension", "XTEST", "-ac",
    ], stdout=xvfb_log, stderr=subprocess.STDOUT, env=env)
    env["DISPLAY"] = ":99"
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        if xvfb.poll() is not None:
            raise RuntimeError("Xvfb failed to start")
        if subprocess.run(["xset", "q"], env=env, stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL, check=False).returncode == 0:
            break
        time.sleep(0.05)
    else:
        raise TimeoutError("Xvfb did not become ready for xset")
    if xvfb.poll() is not None:
        raise RuntimeError("Xvfb failed to start")
    subprocess.run(["xset", "+fp", "/usr/share/fonts/X11/misc"], env=env, check=True)
    subprocess.run(["xset", "fp", "rehash"], env=env, check=True)
    wm = subprocess.Popen(["openbox"], stdout=wm_log, stderr=subprocess.STDOUT, env=env)
    time.sleep(0.5)
    if wm.poll() is not None:
        raise RuntimeError("Openbox failed to start")
    return [xvfb, wm]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path)
    p.add_argument("--allocation", default="issue4448-construction-pilot-02")
    p.add_argument("--child", action="store_true")
    p.add_argument("--effect", type=Path)
    p.add_argument("--ready", type=Path)
    p.add_argument("--arm", choices=["resident", "ephemeral"])
    p.add_argument("--count", type=int, default=1)
    args = p.parse_args()
    if args.child:
        try:
            return child(args.effect, args.ready, args.arm, args.count)
        except BaseException:
            (args.effect.parent / "child-exception.txt").write_text(traceback.format_exc())
            raise
    if not args.output:
        p.error("--output is required")
    args.output.mkdir(parents=True, exist_ok=False)
    os.environ["DISPLAY"] = ":99"
    processes = start_display(args.output)
    try:
        dpy = display.Display()
        if not dpy.query_extension("XTEST").present:
            raise RuntimeError("XTEST extension unavailable")
        dpy.close()
        first = run_arm("ephemeral", "pair01", args.output)
        second = run_arm("resident", "pair01", args.output)
        result = {
            "allocation": args.allocation,
            "classification": "CONSTRUCTION_ONLY_NOT_FORMAL",
            "display": ":99", "arm_order": ["ephemeral", "resident"],
            "processes": {"xvfb": processes[0].pid, "openbox": processes[1].pid},
            "arms": [first, second],
        }
        (args.output / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps({
            "allocation": result["allocation"],
            "actions": [len(x["actions"]) for x in result["arms"]],
            "effects": [len(x["effect_records"]) for x in result["arms"]],
            "release": [x["release_verified"] for x in result["arms"]],
            "session_wall_ns": [x["session_wall_ns"] for x in result["arms"]],
        }, sort_keys=True))
    finally:
        for proc in reversed(processes):
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=3)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
