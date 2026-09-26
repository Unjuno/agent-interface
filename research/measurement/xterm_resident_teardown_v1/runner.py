from __future__ import annotations

import argparse
import hashlib
import json
import os
import select
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from Xlib import X, XK, display
from Xlib.ext import xtest


FORMAL_SCHEDULE_ID = "xterm-resident-teardown-20260927-r1"
FORMAL_PAIRS = 12
FORMAL_ACTIONS = 4
EFFECT_TIMEOUT_S = 3.0
CHILD = Path(__file__).with_name("fixture_child.py")


def descendants(root):
    todo = list(root.query_tree().children)
    while todo:
        item = todo.pop()
        yield item
        try:
            todo.extend(item.query_tree().children)
        except Exception:
            pass


def start_display(root: Path, with_wm: bool = True):
    runtime_root = Path(tempfile.mkdtemp(prefix="ai4448-runtime-", dir="/tmp"))
    home = runtime_root / "home"
    home.mkdir()
    auth = runtime_root / "Xauthority"
    auth.write_bytes(b"")
    os.chmod(auth, 0o600)
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["XDG_CONFIG_HOME"] = str(home / ".config")
    env["XDG_CACHE_HOME"] = str(home / ".cache")
    env["XAUTHORITY"] = str(auth)
    xvfb_stderr = (root / "xvfb.stderr").open("wb")
    xvfb = subprocess.Popen(
        ["Xvfb", "-displayfd", "1", "-screen", "0", "800x600x24", "-nolisten", "tcp", "-ac"],
        stdout=subprocess.PIPE, stderr=xvfb_stderr, text=True, env=env,
    )
    xvfb_stderr.close()
    readable, _, _ = select.select([xvfb.stdout], [], [], 5)
    if not readable:
        raise RuntimeError("Xvfb displayfd startup exceeded 5 seconds")
    number = xvfb.stdout.readline().strip()
    if not number:
        raise RuntimeError("Xvfb failed to allocate display")
    env["DISPLAY"] = ":" + number
    wm_log = (root / "openbox.stderr").open("wb") if with_wm else None
    wm = subprocess.Popen(["openbox"], stdout=subprocess.DEVNULL, stderr=wm_log, env=env) if with_wm else None
    if wm_log is not None:
        wm_log.close()
    if wm is not None:
        deadline = time.monotonic() + 5
        ready = False
        probe = display.Display(env["DISPLAY"])
        root_window = probe.screen().root
        check_atom = probe.intern_atom("_NET_SUPPORTING_WM_CHECK")
        while time.monotonic() < deadline:
            if wm.poll() is not None:
                probe.close()
                raise RuntimeError(f"Openbox exited during startup: {wm.returncode}")
            prop = root_window.get_full_property(check_atom, X.AnyPropertyType)
            if prop is not None and len(prop.value) == 1:
                check_id = int(prop.value[0])
                check_window = probe.create_resource_object("window", check_id)
                self_prop = check_window.get_full_property(check_atom, X.AnyPropertyType)
                if self_prop is not None and len(self_prop.value) == 1 and int(self_prop.value[0]) == check_id:
                    ready = True
                    break
            time.sleep(.025)
        probe.close()
        if not ready:
            raise RuntimeError("Openbox EWMH self-check did not become ready within 5 seconds")
        # EWMH properties are published before Openbox's first MapRequest cycle is fully serviced.
        time.sleep(.75)
    return xvfb, wm, env


def start_terminal(env, effect: Path, title: str, action_limit: int, stderr_path: Path):
    child_env = env.copy()
    ready_path = effect.with_suffix(".ready.json")
    done_path = effect.with_suffix(".done.json")
    with stderr_path.open("wb") as err:
        proc = subprocess.Popen(
            ["xterm", "-geometry", "50x12+20+20", "-fn", "fixed", "-b", "0", "-title", title,
             "-e", sys.executable, str(CHILD), "--effect", str(effect), "--ready", str(ready_path),
             "--done", str(done_path), "--limit", str(action_limit)],
            env=child_env, stdout=subprocess.DEVNULL, stderr=err,
        )
    d = display.Display(env["DISPLAY"])
    deadline = time.monotonic() + 5
    window = None
    while time.monotonic() < deadline:
        for candidate in descendants(d.screen().root):
            try:
                if candidate.get_wm_name() == title and candidate.get_attributes().map_state == X.IsViewable:
                    window = candidate
                    break
            except Exception:
                pass
        if window:
            break
        if proc.poll() is not None:
            raise RuntimeError(f"xterm exited during startup: {proc.returncode}")
        time.sleep(.01)
    if window is None:
        names = []
        for candidate in descendants(d.screen().root):
            try:
                names.append((repr(candidate.get_wm_name()), candidate.get_attributes().map_state, candidate.query_tree().parent.id))
            except Exception:
                pass
        wmctl = subprocess.run(["wmctrl", "-l"], env=env, capture_output=True, text=True).stdout
        raise RuntimeError(f"XTerm window did not become viewable; rc={proc.poll()}; names={names}; wmctrl={wmctl}; stderr={stderr_path.read_text(errors='replace')}")
    window.set_input_focus(X.RevertToParent, X.CurrentTime)
    d.sync()
    ready_deadline = time.monotonic() + 3
    while time.monotonic() < ready_deadline and not ready_path.exists() and proc.poll() is None:
        time.sleep(.005)
    if not ready_path.exists():
        process = subprocess.run(["ps", "-eo", "pid,ppid,args"], capture_output=True, text=True).stdout
        listing = subprocess.run(["xwininfo", "-root", "-tree"], env=env, capture_output=True, text=True).stdout
        raise RuntimeError(f"XTerm child did not write readiness after window activation; rc={proc.poll()}; process={process}; tree={listing}; stderr={stderr_path.read_text(errors='replace')}")
    d.sync()
    child_pid = json.loads(ready_path.read_text())["pid"]
    return proc, d, child_pid, ready_path, done_path


def query_key_state(d):
    state = bytes(d.query_keymap())
    codes = {name: d.keysym_to_keycode(XK.string_to_keysym(name)) for name in ("r", "Return")}
    pressed = {name: bool(state[code // 8] & (1 << (code % 8))) for name, code in codes.items()}
    return state, codes, pressed


def send_return(d):
    char = d.keysym_to_keycode(XK.string_to_keysym("r"))
    code = d.keysym_to_keycode(XK.string_to_keysym("Return"))
    xtest.fake_input(d, X.KeyPress, char)
    d.sync()
    xtest.fake_input(d, X.KeyRelease, char)
    d.sync()
    xtest.fake_input(d, X.KeyPress, code)
    d.sync()
    xtest.fake_input(d, X.KeyRelease, code)
    d.sync()


def wait_effect(path: Path, expected_count: int, proc=None, stderr_path: Path | None = None):
    deadline = time.monotonic() + EFFECT_TIMEOUT_S
    while time.monotonic() < deadline:
        if path.exists():
            rows = [json.loads(line) for line in path.read_text().splitlines() if line]
            if len(rows) >= expected_count:
                return time.perf_counter_ns(), rows
        time.sleep(.001)
    details = f"; child_rc={proc.poll()}" if proc is not None else ""
    if stderr_path is not None and stderr_path.exists():
        details += f"; stderr={stderr_path.read_text(errors='replace')}"
    raise RuntimeError(f"effect timeout at row {expected_count}{details}")


def kill_wait(proc):
    if proc.poll() is None:
        proc.terminate()
    try:
        return proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()
        return proc.wait(timeout=2)


def run_arm(pair_dir: Path, env, pair: int, arm: str):
    arm_dir = pair_dir / arm
    arm_dir.mkdir()
    rows = []
    resident = arm == "RESIDENT_XTERM"
    started = time.perf_counter_ns()
    proc = d = None
    pid = None
    try:
        total = FORMAL_ACTIONS
        for action in range(total):
            effect = arm_dir / ("effects.jsonl" if resident else f"effects-{action}.jsonl")
            title = f"AI4448-{pair}-{arm}-{action}"
            if proc is None:
                proc, d, child_pid, ready_path, done_path = start_terminal(env, effect, title, total if resident else 1, arm_dir / f"xterm-{action}.stderr")
                pid = proc.pid
            elif proc.poll() is not None:
                raise RuntimeError("resident terminal exited before final action")
            send_return(d)
            observed_ns, observed = wait_effect(effect, action + 1 if resident else 1, proc, arm_dir / f"xterm-{action}.stderr")
            effect_index = action if resident else 0
            if observed[effect_index] != {"value": "r"}:
                raise RuntimeError("effect bytes mismatch")
            observed_effect_bytes = effect.read_bytes()
            deadline = time.monotonic() + 1
            state, keycodes, pressed = query_key_state(d)
            while any(pressed.values()) and time.monotonic() < deadline:
                time.sleep(.001)
                state, keycodes, pressed = query_key_state(d)
            key_up_ns = time.perf_counter_ns()
            if any(state):
                raise RuntimeError("X server keymap was not neutral")
            if not resident:
                exit_code = proc.wait(timeout=3)
                exited_ns = time.perf_counter_ns()
                done_record = json.loads(done_path.read_text())
                proc = None
                pid_for_action = pid
                pid = None
                ready_ns = exited_ns
                d.close()
                d = None
            else:
                exit_code = None
                pid_for_action = pid
                ready_ns = key_up_ns
            rows.append({
                "pair": pair, "arm": arm, "action": action,
                "input_keys": ["r", "Return"],
                "effect_observed_ns": observed_ns, "key_up_ns": key_up_ns,
                "next_ready_ns": ready_ns, "latency_ns": ready_ns - observed_ns,
                "terminal_pid": pid_for_action, "terminal_exit_after_action": exit_code,
                "child_pid": child_pid,
                "terminal_exit_ns": exited_ns if not resident else None,
                "keymap_hex": state.hex(), "keycodes": keycodes,
                "effect_bytes_hex": observed_effect_bytes.hex(),
                "effect_sha256": hashlib.sha256(observed_effect_bytes).hexdigest(),
                "ready_record": json.loads(ready_path.read_text()),
                "done_record": done_record if not resident else None,
                "key_up": True,
            })
        if resident:
            exit_code = proc.wait(timeout=3)
            exited_ns = time.perf_counter_ns()
            done_record = json.loads(done_path.read_text())
            rows[-1]["terminal_exit_after_action"] = exit_code
            rows[-1]["terminal_exit_ns"] = exited_ns
            rows[-1]["done_record"] = done_record
        else:
            exit_code = rows[-1]["terminal_exit_after_action"]
    finally:
        if d is not None:
            d.close()
        if proc is not None:
            kill_wait(proc)
    ended = time.perf_counter_ns()
    return {"pair": pair, "arm": arm, "rows": rows, "started_ns": started,
            "ended_ns": ended, "session_ns": ended - started, "terminal_exit": exit_code}


def run_all(output: Path, pairs: int, schedule_id: str, label: str, with_wm: bool):
    output.mkdir(parents=True, exist_ok=False)
    schedule = []
    for pair in range(pairs):
        order = ["EPHEMERAL_XTERM", "RESIDENT_XTERM"]
        if pair % 2:
            order.reverse()
        schedule.append({"pair": pair, "order": order})
    records = []
    errors = []
    root = output / "scratch"
    root.mkdir()
    for item in schedule:
            pair = item["pair"]
            pair_dir = root / f"pair-{pair:02d}"
            pair_dir.mkdir()
            xvfb, wm, env = start_display(pair_dir, with_wm)
            result = {"pair": pair, "order": item["order"], "xvfb_pid": xvfb.pid,
                      "wm_pid": wm.pid if wm is not None else None, "arms": []}
            try:
                for arm in item["order"]:
                    result["arms"].append(run_arm(pair_dir, env, pair, arm))
            except Exception as exc:
                errors.append({"pair": pair, "error": repr(exc)})
            finally:
                result["wm_exit"] = kill_wait(wm) if wm is not None else None
                result["xvfb_exit"] = kill_wait(xvfb)
            records.append(result)
    payload = {"label": label, "schedule_id": schedule_id, "pairs_planned": pairs,
               "formal_invocations": 1 if label == "formal" else 0,
               "reruns": 0, "replacements": 0, "tuning": 0,
               "with_window_manager": with_wm,
               "actions_per_arm": FORMAL_ACTIONS, "schedule": schedule,
               "pairs": records, "errors": errors}
    (output / "raw.json").write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"output": str(output), "pairs": pairs, "errors": errors}, sort_keys=True))
    return 0 if not errors and len(records) == pairs else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pairs", type=int, default=FORMAL_PAIRS)
    parser.add_argument("--schedule-id", default=FORMAL_SCHEDULE_ID)
    parser.add_argument("--label", default="construction-excluded")
    parser.add_argument("--without-wm", action="store_true", help="diagnostic only; not eligible for formal results")
    args = parser.parse_args()
    raise SystemExit(run_all(args.output, args.pairs, args.schedule_id, args.label, not args.without_wm))


if __name__ == "__main__":
    main()
