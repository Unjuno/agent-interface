from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
import subprocess
import threading
import time
from pathlib import Path

import tkinter as tk
from Xlib import X, XK, display
from Xlib.ext import xtest

from candidate import ALLOWED, select_disposition
from fixture import (
    CLEAR, WATCH, HARD, STATE_COLOR,
    WIDTH, HEIGHT, SENTINEL, PROGRESS_RECT, HARM_RECT,
    LiveFixture,
)

TASK = "CONCURRENT-FAST-DECISION-T1-X11-20260918-001"
FRONTIER_RETURN_NS = 40_000_000
SAMPLE_NS = 5_000_000
ACTIVATE_DEADLINE_NS = 12_000_000
YIELD_DEADLINE_NS = 10_000_000
CONTROLLER_RECT = (SENTINEL[0], SENTINEL[1], 1, 1)
PROGRESS_SCORE_RECT = (PROGRESS_RECT[0], PROGRESS_RECT[1], PROGRESS_RECT[2]-PROGRESS_RECT[0], PROGRESS_RECT[3]-PROGRESS_RECT[1])
HARM_SCORE_RECT = (HARM_RECT[0], HARM_RECT[1], HARM_RECT[2]-HARM_RECT[0], HARM_RECT[3]-HARM_RECT[1])
RGB_TO_STATE = {
    (0, 255, 0): CLEAR,
    (255, 255, 0): WATCH,
    (255, 0, 0): HARD,
}

FORMAL_SCENARIOS = (
    {"name":"ACTIVATE_8", "initial":WATCH, "transitions":((8_000_000,CLEAR),(20_000_000,WATCH))},
    {"name":"INVALIDATE_18", "initial":CLEAR, "transitions":((18_000_000,HARD),)},
    {"name":"TRANSIENT_28", "initial":CLEAR, "transitions":((28_000_000,WATCH),(40_000_000,CLEAR))},
    {"name":"ACTIVATE_18", "initial":WATCH, "transitions":((18_000_000,CLEAR),(30_000_000,WATCH))},
    {"name":"INVALIDATE_28", "initial":CLEAR, "transitions":((28_000_000,HARD),)},
    {"name":"TRANSIENT_8", "initial":CLEAR, "transitions":((8_000_000,WATCH),(20_000_000,CLEAR))},
)
CONSTRUCTION_SCENARIOS = (
    {"name":"ACTIVATE_18_CONSTRUCTION", "initial":WATCH, "transitions":((18_000_000,CLEAR),(30_000_000,WATCH))},
)
ARMS = ("FRONTIER_BOUNDARY_ONLY", "DETERMINISTIC_FAST_LANE")


def sleep_until_ns(target: int) -> None:
    while True:
        rem = target - time.perf_counter_ns()
        if rem <= 0:
            return
        if rem > 2_000_000:
            time.sleep((rem - 500_000) / 1e9)
        elif rem > 100_000:
            time.sleep(rem / 2e9)


def start_xvfb(case_root: Path):
    auth = case_root / "Xauthority"
    auth.write_bytes(b"")
    os.chmod(auth, 0o600)
    env = os.environ.copy()
    env["XAUTHORITY"] = str(auth)
    proc = subprocess.Popen(
        ["Xvfb", "-displayfd", "1", "-screen", "0", "640x480x24", "-nolisten", "tcp", "-pn", "-ac"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env,
    )
    line = proc.stdout.readline().strip()
    if not line:
        raise RuntimeError("Xvfb displayfd failed")
    env["DISPLAY"] = ":" + line
    return proc, env


def descendants(root):
    out = []
    queue = list(root.query_tree().children)
    for _ in range(5):
        nxt = []
        for w in queue:
            out.append(w)
            try:
                nxt.extend(w.query_tree().children)
            except Exception:
                pass
        queue = nxt
    return out


def find_window(D, title: str, timeout=3.0):
    end = time.monotonic() + timeout
    root = D.screen().root
    while time.monotonic() < end:
        for w in descendants(root):
            try:
                if w.get_wm_name() == title and w.get_attributes().map_state == X.IsViewable:
                    return w
            except Exception:
                pass
        time.sleep(0.005)
    raise RuntimeError("fixture window not found")


def decode_pixel(data: bytes) -> tuple[int,int,int]:
    if len(data) != 4:
        raise RuntimeError(f"sentinel bytes={len(data)}")
    b, g, r, _ = data
    return (r, g, b)


def sample_state(win) -> tuple[int,int,str,tuple[int,int,int]]:
    b = time.perf_counter_ns()
    img = win.get_image(*CONTROLLER_RECT, X.ZPixmap, 0xffffffff)
    e = time.perf_counter_ns()
    rgb = decode_pixel(bytes(img.data))
    state = RGB_TO_STATE.get(rgb)
    if state is None:
        raise RuntimeError(f"unknown sentinel rgb={rgb}")
    return b, e, state, rgb


def send_f8(D, keycode: int) -> tuple[int,int]:
    b = time.perf_counter_ns()
    xtest.fake_input(D, X.KeyPress, keycode)
    xtest.fake_input(D, X.KeyRelease, keycode)
    D.sync()
    e = time.perf_counter_ns()
    return b, e


def query_key_up(D, keycode: int) -> bool:
    keys = D.query_keymap()
    raw = keys if isinstance(keys, (bytes, bytearray)) else bytes(keys)
    idx = keycode // 8
    bit = keycode % 8
    return (raw[idx] & (1 << bit)) == 0


def count_color(win, rect, rgb: tuple[int,int,int]) -> int:
    img = win.get_image(*rect, X.ZPixmap, 0xffffffff)
    data = bytes(img.data)
    if len(data) != rect[2] * rect[3] * 4:
        raise RuntimeError("score bytes mismatch")
    n = 0
    for i in range(0, len(data), 4):
        b,g,r,_ = data[i:i+4]
        if (r,g,b) == rgb:
            n += 1
    return n


def expected_state_at(scenario: dict, elapsed_ns: int) -> str:
    state = scenario["initial"]
    for off, nxt in scenario["transitions"]:
        if elapsed_ns >= off:
            state = nxt
        else:
            break
    return state


def pure_expected_samples(scenario: dict) -> list[tuple[int,str,str]]:
    out = []
    for off in range(0, FRONTIER_RETURN_NS, SAMPLE_NS):
        state = expected_state_at(scenario, off)
        disp = select_disposition(state)
        out.append((off, state, disp))
        if disp == "YIELD":
            break
    return out


def schedule_transitions(root: tk.Tk, fixture: LiveFixture, scenario: dict, start_ns: int, stop_evt: threading.Event):
    def worker():
        for off, state in scenario["transitions"]:
            if stop_evt.is_set():
                return
            sleep_until_ns(start_ns + off)
            if stop_evt.is_set():
                return
            root.after(0, lambda s=state, o=off: fixture.set_state(s, o))
    t = threading.Thread(target=worker, name="transition-scheduler", daemon=True)
    t.start()
    return t


def run_session(root_dir: Path, pair_id: int, arm: str, scenario: dict, order_pos: int):
    case_id = f"p{pair_id:02d}-{order_pos}-{arm}-{scenario['name']}"
    cr = root_dir / case_id
    cr.mkdir(parents=True, exist_ok=False)
    xvfb = None
    root = None
    control_D = None
    scorer_D = None
    prior_display = os.environ.get("DISPLAY")
    prior_xauth = os.environ.get("XAUTHORITY")
    cleanup = {"xvfb_exit":False, "tk_destroyed":False, "control_closed":False, "scorer_closed":False}
    exceptions = []
    samples = []
    sends = []
    event_log = []
    transition_thread = None
    controller_thread = None
    stop_evt = threading.Event()
    meta = {}
    try:
        xvfb, env = start_xvfb(cr)
        os.environ["DISPLAY"] = env["DISPLAY"]
        os.environ["XAUTHORITY"] = env["XAUTHORITY"]
        title = "AI1384-" + case_id
        root = tk.Tk()
        root.title(title)
        root.geometry(f"{WIDTH}x{HEIGHT}+20+20")
        root.resizable(False, False)
        fixture = LiveFixture(root, scenario["initial"], event_log)
        root.update_idletasks(); root.update()

        control_D = display.Display(env["DISPLAY"])
        scorer_D = display.Display(env["DISPLAY"])
        control_win = find_window(control_D, title)
        scorer_win = find_window(scorer_D, title)
        control_win.set_input_focus(X.RevertToParent, X.CurrentTime)
        control_D.sync()
        keycode = control_D.keysym_to_keycode(XK.string_to_keysym("F8"))
        if not keycode:
            raise RuntimeError("F8 keycode unavailable")
        # Confirm only the frozen sentinel pixel is visible to the controller before measurement.
        _, _, initial_decoded, initial_rgb = sample_state(control_win)
        if initial_decoded != scenario["initial"]:
            raise RuntimeError(f"initial sentinel mismatch {initial_decoded} != {scenario['initial']}")

        start_ns = time.perf_counter_ns() + 20_000_000
        meta = {
            "case_id":case_id, "pair_id":pair_id, "arm":arm, "scenario":scenario["name"],
            "initial_state":scenario["initial"], "nominal_transitions":[list(x) for x in scenario["transitions"]],
            "frontier_request_offset_ns":0, "frontier_return_offset_ns":FRONTIER_RETURN_NS,
            "start_ns":start_ns, "keycode":keycode,
            "controller_capture_rect":list(CONTROLLER_RECT),
            "progress_score_rect":list(PROGRESS_SCORE_RECT), "harm_score_rect":list(HARM_SCORE_RECT),
            "initial_rgb":list(initial_rgb),
        }
        transition_thread = schedule_transitions(root, fixture, scenario, start_ns, stop_evt)

        def controller():
            sleep_until_ns(start_ns)
            if arm == "FRONTIER_BOUNDARY_ONLY":
                sleep_until_ns(start_ns + FRONTIER_RETURN_NS)
                return
            for off in range(0, FRONTIER_RETURN_NS, SAMPLE_NS):
                if stop_evt.is_set():
                    return
                sleep_until_ns(start_ns + off)
                sb, se, state, rgb = sample_state(control_win)
                d0 = time.perf_counter_ns(); disp = select_disposition(state); d1 = time.perf_counter_ns()
                row = {
                    "nominal_sample_offset_ns":off, "sample_begin_ns":sb, "sample_end_ns":se,
                    "sample_duration_ns":se-sb, "state":state, "rgb":list(rgb),
                    "disposition":disp, "decision_begin_ns":d0, "decision_end_ns":d1,
                    "decision_compute_ns":d1-d0,
                }
                samples.append(row)
                if disp not in ALLOWED:
                    raise RuntimeError("out-of-vocabulary disposition")
                if disp == "ADVANCE":
                    ab, ae = send_f8(control_D, keycode)
                    sends.append({"nominal_sample_offset_ns":off, "send_begin_ns":ab, "send_end_ns":ae, "send_duration_ns":ae-ab})
                    row["send_index"] = len(sends)-1
                elif disp == "YIELD":
                    row["terminal_yield"] = True
                    return
        controller_thread = threading.Thread(target=controller, name="controller", daemon=True)
        controller_thread.start()

        end_ns = start_ns + FRONTIER_RETURN_NS
        while time.perf_counter_ns() < end_ns or controller_thread.is_alive():
            root.update()
            time.sleep(0.0002)
            if time.perf_counter_ns() > end_ns + 20_000_000:
                raise RuntimeError("controller overrun")
        controller_thread.join(timeout=0.1)
        stop_evt.set()
        if transition_thread is not None:
            transition_thread.join(timeout=0.1)
        # Process any already queued key release / transition callbacks before scoring.
        for _ in range(5):
            root.update(); time.sleep(0.001)
        frontier_return_actual_ns = time.perf_counter_ns()

        progress_pixels = count_color(scorer_win, PROGRESS_SCORE_RECT, (0,255,0))
        harm_pixels = count_color(scorer_win, HARM_SCORE_RECT, (255,0,0))
        terminal_f8_up = query_key_up(scorer_D, keycode)
        transition_rows = [e for e in event_log if e.get("event") == "state_transition"]
        effect_rows = [e for e in event_log if e.get("event") == "f8_effect"]
        press_rows = [e for e in event_log if e.get("event") == "f8_press"]
        release_rows = [e for e in event_log if e.get("event") == "f8_release"]
        result = {
            **meta,
            "frontier_return_actual_ns":frontier_return_actual_ns,
            "samples":samples, "sends":sends, "fixture_events":event_log,
            "actual_transitions":transition_rows, "effects":effect_rows, "presses":press_rows, "releases":release_rows,
            "score":{"progress_pixels":progress_pixels, "harm_pixels":harm_pixels},
            "terminal_f8_up":terminal_f8_up,
            "exceptions":exceptions, "cleanup":cleanup,
        }
        return result
    except Exception as exc:
        exceptions.append({"type":type(exc).__name__, "message":str(exc)})
        return {**meta, "case_id":case_id, "pair_id":pair_id, "arm":arm, "scenario":scenario["name"], "samples":samples, "sends":sends, "fixture_events":event_log, "exceptions":exceptions, "cleanup":cleanup}
    finally:
        stop_evt.set()
        if controller_thread is not None:
            controller_thread.join(timeout=0.2)
        if transition_thread is not None:
            transition_thread.join(timeout=0.2)
        if control_D is not None:
            try: control_D.close(); cleanup["control_closed"] = True
            except Exception: pass
        if scorer_D is not None:
            try: scorer_D.close(); cleanup["scorer_closed"] = True
            except Exception: pass
        if root is not None:
            try: root.destroy(); cleanup["tk_destroyed"] = True
            except Exception: pass
        if xvfb is not None:
            try:
                xvfb.terminate(); xvfb.wait(timeout=2); cleanup["xvfb_exit"] = True
            except Exception:
                try: xvfb.kill(); xvfb.wait(timeout=1); cleanup["xvfb_exit"] = True
                except Exception: pass
        if prior_display is None: os.environ.pop("DISPLAY", None)
        else: os.environ["DISPLAY"] = prior_display
        if prior_xauth is None: os.environ.pop("XAUTHORITY", None)
        else: os.environ["XAUTHORITY"] = prior_xauth


def summarize(cases: list[dict]) -> dict:
    return {
        "sessions":len(cases),
        "candidate_progress_pixels":sum(c.get("score",{}).get("progress_pixels",0) for c in cases if c.get("arm")=="DETERMINISTIC_FAST_LANE"),
        "baseline_progress_pixels":sum(c.get("score",{}).get("progress_pixels",0) for c in cases if c.get("arm")=="FRONTIER_BOUNDARY_ONLY"),
        "candidate_harm_pixels":sum(c.get("score",{}).get("harm_pixels",0) for c in cases if c.get("arm")=="DETERMINISTIC_FAST_LANE"),
        "baseline_harm_pixels":sum(c.get("score",{}).get("harm_pixels",0) for c in cases if c.get("arm")=="FRONTIER_BOUNDARY_ONLY"),
        "terminal_f8_up":sum(bool(c.get("terminal_f8_up")) for c in cases),
        "exceptions":sum(bool(c.get("exceptions")) for c in cases),
        "cleanup_complete":sum(all(c.get("cleanup",{}).get(k) for k in ("xvfb_exit","tk_destroyed","control_closed","scorer_closed")) for c in cases),
    }


def run(formal: bool, out: Path, root_dir: Path):
    if out.exists():
        raise SystemExit("result exists")
    scenarios = FORMAL_SCENARIOS if formal else CONSTRUCTION_SCENARIOS
    cases=[]
    for pair_id, scenario in enumerate(scenarios):
        order = ARMS if pair_id % 2 == 0 else tuple(reversed(ARMS))
        for pos, arm in enumerate(order):
            cases.append(run_session(root_dir, pair_id, arm, scenario, pos))
    result = {
        "task":TASK, "phase":"formal" if formal else "construction",
        "formal_invocations":1 if formal else 0, "reruns":0, "replacements":0, "tuning":0,
        "frontier_schedule":{"request_ns":0,"return_ns":FRONTIER_RETURN_NS},
        "sample_period_ns":SAMPLE_NS,
        "pairs":len(scenarios), "cases":cases, "summary":summarize(cases),
    }
    out.write_text(json.dumps(result, indent=2, sort_keys=True)+"
")
    print(json.dumps(result["summary"], sort_keys=True))


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--formal",action="store_true"); ap.add_argument("--out",required=True); ap.add_argument("--root",required=True); ap.add_argument("--pure",action="store_true")
    a=ap.parse_args()
    if a.pure:
        data={s["name"]:pure_expected_samples(s) for s in FORMAL_SCENARIOS}
        print(json.dumps(data,sort_keys=True)); return
    root_dir=Path(a.root); root_dir.mkdir(parents=True,exist_ok=False)
    run(a.formal, Path(a.out), root_dir)

if __name__ == "__main__":
    main()
