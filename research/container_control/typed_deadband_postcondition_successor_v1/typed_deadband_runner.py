#!/usr/bin/env python3
"""Container/X11 typed-deadband successor: coast vs bounded recovery with task-relative cancellation.

This is deliberately model-free: planner latency is simulated with a fixed sleep so
that the experiment isolates the interface mechanism. The controller observes only
rendered pixels. Exact state is written by the app to a scorer-only stream and is
read only after the controller exits.
"""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, statistics, subprocess, sys, time
from pathlib import Path
import tkinter as tk
from Xlib import X, XK, display
from Xlib.ext import xtest

WIDTH, HEIGHT = 800, 300
TRACK_L, TRACK_R = 60, 740
CENTER_Y = 140
SAFE_ABS = 0.55
CENTER_ABS = 0.12
FPS_MS = 16
APP_TAIL_S = 0.35


def x_to_px(x: float) -> int:
    return int(TRACK_L + (x + 1.0) * 0.5 * (TRACK_R - TRACK_L))


def px_to_x(px: float) -> float:
    return ((px - TRACK_L) / (TRACK_R - TRACK_L)) * 2.0 - 1.0


class TaskApp:
    def __init__(self, out: Path, duration: float):
        self.out = out
        self.duration = duration
        self.root = tk.Tk()
        self.root.title("AI-Recovery-Benchmark")
        self.root.geometry(f"{WIDTH}x{HEIGHT}+0+0")
        self.root.resizable(False, False)
        self.canvas = tk.Canvas(self.root, width=WIDTH, height=HEIGHT, bg="white", highlightthickness=0)
        self.canvas.pack()
        self.canvas.create_rectangle(x_to_px(-SAFE_ABS), 100, x_to_px(SAFE_ABS), 180, outline="gray", width=2)
        self.canvas.create_line(x_to_px(0), 90, x_to_px(0), 190, fill="black")
        self.marker = self.canvas.create_rectangle(0, 0, 0, 0, fill="#ff0033", outline="")
        self.x = 0.43
        self.left = False
        self.right = False
        self.start_ns = None
        self.last_ns = None
        self.rows: list[dict] = []
        self.input_rows: list[dict] = []
        self.root.bind("<KeyPress-Left>", lambda _e: self.set_key("left", True))
        self.root.bind("<KeyRelease-Left>", lambda _e: self.set_key("left", False))
        self.root.bind("<KeyPress-Right>", lambda _e: self.set_key("right", True))
        self.root.bind("<KeyRelease-Right>", lambda _e: self.set_key("right", False))
        self.root.after(100, self.begin)

    def set_key(self, key: str, down: bool) -> None:
        setattr(self, key, down)
        self.input_rows.append({"ns": time.monotonic_ns(), "key": key, "down": down})

    @staticmethod
    def drift(t_s: float) -> float:
        # A deterministic exogenous disturbance independent of controller arm.
        if t_s < 0.85:
            return 0.34
        if t_s < 1.55:
            return -0.42
        return 0.31

    def begin(self) -> None:
        self.start_ns = self.last_ns = time.monotonic_ns()
        self.tick()

    def tick(self) -> None:
        now = time.monotonic_ns()
        t_s = (now - self.start_ns) / 1e9
        dt = (now - self.last_ns) / 1e9
        self.last_ns = now
        control = (-0.72 if self.left else 0.0) + (0.72 if self.right else 0.0)
        self.x += (self.drift(t_s) + control) * dt
        self.x = max(-0.98, min(0.98, self.x))
        px = x_to_px(self.x)
        self.canvas.coords(self.marker, px - 9, CENTER_Y - 18, px + 9, CENTER_Y + 18)
        self.rows.append({
            "ns": now,
            "t_s": t_s,
            "x": self.x,
            "safe": abs(self.x) <= SAFE_ABS,
            "center": abs(self.x) <= CENTER_ABS,
            "left": self.left,
            "right": self.right,
        })
        if (self.out / "stop.flag").exists() or t_s >= self.duration:
            self.finish()
            return
        self.root.after(FPS_MS, self.tick)

    def finish(self) -> None:
        self.out.mkdir(parents=True, exist_ok=True)
        (self.out / "score.jsonl").write_text("\n".join(json.dumps(r, separators=(",", ":")) for r in self.rows) + "\n")
        (self.out / "input.jsonl").write_text("\n".join(json.dumps(r, separators=(",", ":")) for r in self.input_rows) + "\n")
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def capture_marker(d, win) -> tuple[float | None, int]:
    try:
        g = win.get_geometry()
        raw = win.get_image(0, 0, g.width, g.height, X.ZPixmap, 0xFFFFFFFF)
    except Exception:
        return None, time.monotonic_ns()
    data = raw.data
    xs: list[int] = []
    # Xvfb 24/32 is B,G,R,pad in this container. Scan only the task band.
    for y in range(100, 181, 3):
        for x in range(TRACK_L, TRACK_R + 1, 2):
            i = (y * g.width + x) * 4
            if i + 2 >= len(data):
                continue
            b, green, r = data[i], data[i + 1], data[i + 2]
            if r > 220 and green < 70 and b < 100:
                xs.append(x)
    observed_ns = time.monotonic_ns()
    if not xs:
        return None, observed_ns
    return px_to_x(sum(xs) / len(xs)), observed_ns


def keycode(d, name: str) -> int:
    return d.keysym_to_keycode(XK.string_to_keysym(name))


def send_key(d, name: str, down: bool, log: list[dict]) -> None:
    start_ns = time.monotonic_ns()
    xtest.fake_input(d, X.KeyPress if down else X.KeyRelease, keycode(d, name))
    d.sync()
    end_ns = time.monotonic_ns()
    log.append({"kind": "key", "key": name.lower(), "down": down, "call_start_ns": start_ns, "call_end_ns": end_ns})


def release_all(d, held: set[str], log: list[dict], reason: str) -> None:
    for key in sorted(list(held)):
        send_key(d, key, False, log)
        held.remove(key)
    log.append({"kind": "release_all", "reason": reason, "ns": time.monotonic_ns()})


def find_window(d):
    root = d.screen().root
    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline:
        for w in root.query_tree().children:
            try:
                if w.get_wm_name() == "AI-Recovery-Benchmark":
                    return w
            except Exception:
                pass
        time.sleep(0.02)
    raise RuntimeError("task window not found")


def controller(out: Path, mode: str, decisions: int, planner_wait_s: float, cover_budget_s: float, deadband_abs: float) -> None:
    d = display.Display()
    win = find_window(d)
    win.set_input_focus(X.RevertToParent, X.CurrentTime)
    d.sync()
    held: set[str] = set()
    log: list[dict] = []
    previous_policy: str | None = None
    time.sleep(0.12)
    control_start_ns = time.monotonic_ns()
    log.append({"kind": "control_start", "ns": control_start_ns})

    for decision in range(1, decisions + 1):
        source_x, source_ns = capture_marker(d, win)
        if source_x is None:
            raise RuntimeError("marker not visible at decision source")
        decision_start_ns = time.monotonic_ns()
        log.append({"kind": "decision_start", "decision": decision, "source_x": source_x, "capture_ns": source_ns, "ns": decision_start_ns})

        if mode == "recovery" and previous_policy:
            key = previous_policy
            valid = (key == "Left" and source_x > deadband_abs) or (key == "Right" and source_x < -deadband_abs)
            if valid:
                log.append({"kind": "cover_admit", "decision": decision, "key": key.lower(), "source_x": source_x, "ns": time.monotonic_ns()})
                send_key(d, key, True, log)
                held.add(key)
                cover_start = time.monotonic()
                while time.monotonic() - cover_start < min(cover_budget_s, planner_wait_s):
                    time.sleep(0.018)
                    x, observed_ns = capture_marker(d, win)
                    if x is None:
                        continue
                    still_valid = (key == "Left" and x > deadband_abs) or (key == "Right" and x < -deadband_abs)
                    bounded = abs(x - source_x) <= 0.30
                    if not still_valid or not bounded:
                        guard_ns = time.monotonic_ns()
                        log.append({
                            "kind": "guard_invalid",
                            "decision": decision,
                            "x": x,
                            "source_x": source_x,
                            "observed_ns": observed_ns,
                            "ns": guard_ns,
                        })
                        release_all(d, held, log, "guard_invalid")
                        break
                if held:
                    release_all(d, held, log, "cover_budget")

        # Complete the fixed planner wait from decision-start, independent of arm.
        remaining = planner_wait_s - (time.monotonic_ns() - decision_start_ns) / 1e9
        if remaining > 0:
            time.sleep(remaining)
        current_x, current_capture_ns = capture_marker(d, win)
        if current_x is None:
            raise RuntimeError("marker not visible at planner return")
        if current_x > 0.10:
            policy = "Left"
        elif current_x < -0.10:
            policy = "Right"
        else:
            policy = None
        previous_policy = policy
        log.append({
            "kind": "planner_return",
            "decision": decision,
            "current_x": current_x,
            "capture_ns": current_capture_ns,
            "policy": policy,
            "ns": time.monotonic_ns(),
        })

        # Identical post-planner pulse in both arms.
        if policy:
            send_key(d, policy, True, log)
            held.add(policy)
            time.sleep(0.085)
            release_all(d, held, log, "planner_pulse")
        else:
            time.sleep(0.085)
        time.sleep(0.02)

    release_all(d, held, log, "terminal")
    log.append({"kind": "control_end", "ns": time.monotonic_ns()})
    out.mkdir(parents=True, exist_ok=True)
    (out / "controller.jsonl").write_text("\n".join(json.dumps(r, separators=(",", ":")) for r in log) + "\n")
    (out / "stop.flag").write_text("controller-complete\n")
    d.close()


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def audit_arm(out: Path) -> dict:
    score = load_jsonl(out / "score.jsonl")
    ctrl = load_jsonl(out / "controller.jsonl")
    inp = load_jsonl(out / "input.jsonl")
    start_ns = next(r["ns"] for r in ctrl if r["kind"] == "control_start")
    end_ns = next(r["ns"] for r in ctrl if r["kind"] == "control_end")
    scoped = [r for r in score if start_ns <= r["ns"] <= end_ns]
    if len(scoped) < 2:
        raise AssertionError("insufficient scorer samples inside controller interval")
    unsafe_ns = sum(b["ns"] - a["ns"] for a, b in zip(scoped, scoped[1:]) if not a["safe"])
    center_ns = sum(b["ns"] - a["ns"] for a, b in zip(scoped, scoped[1:]) if a["center"])

    # Physical app-side key events must balance and end empty.
    state = {"left": False, "right": False}
    for r in inp:
        state[r["key"]] = r["down"]
    terminal_empty = not any(state.values())
    press_count = sum(1 for r in inp if r["down"])
    release_count = sum(1 for r in inp if not r["down"])

    # After guard invalidation there must be no new key-down before the planner return.
    stale_repress = 0
    release_latencies_ms: list[float] = []
    for g in [r for r in ctrl if r["kind"] == "guard_invalid"]:
        planner = next(r for r in ctrl if r["kind"] == "planner_return" and r["decision"] == g["decision"])
        for k in ctrl:
            if k.get("kind") == "key" and k.get("down") and g["ns"] < k["call_start_ns"] < planner["ns"]:
                stale_repress += 1
        releases = [r for r in inp if not r["down"] and r["ns"] >= g["ns"]]
        if releases:
            release_latencies_ms.append((releases[0]["ns"] - g["ns"]) / 1e6)

    # Posthoc visual decoder error against nearest scorer sample. This does not feed controller.
    visual_errors: list[float] = []
    for r in ctrl:
        if r["kind"] not in {"decision_start", "planner_return", "guard_invalid"}:
            continue
        observed_x = r.get("source_x") if r["kind"] == "decision_start" else r.get("current_x") if r["kind"] == "planner_return" else r.get("x")
        obs_ns = r.get("capture_ns", r.get("observed_ns", r["ns"]))
        nearest = min(score, key=lambda s: abs(s["ns"] - obs_ns))
        visual_errors.append(abs(observed_x - nearest["x"]))

    return {
        "control_duration_ms": (end_ns - start_ns) / 1e6,
        "unsafe_ms": unsafe_ns / 1e6,
        "center_ms": center_ns / 1e6,
        "max_abs_x": max(abs(r["x"]) for r in scoped),
        "terminal_empty": terminal_empty,
        "press_count": press_count,
        "release_count": release_count,
        "balanced_app_key_events": press_count == release_count,
        "guard_events": sum(1 for r in ctrl if r["kind"] == "guard_invalid"),
        "guard_to_app_release_ms": release_latencies_ms,
        "stale_repress_before_planner": stale_repress,
        "decision_count": sum(1 for r in ctrl if r["kind"] == "decision_start"),
        "visual_decoder_error_max": max(visual_errors) if visual_errors else None,
    }


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_arm(root: Path, pair: int, mode: str, order_index: int, decisions: int, planner_wait_s: float, cover_budget_s: float, deadband_abs: float, display_num: int) -> dict:
    out = root / f"pair-{pair:02d}-{order_index}-{mode}"
    disp = f":{display_num}"
    xvfb = subprocess.Popen(["Xvfb", disp, "-screen", "0", f"{WIDTH}x{HEIGHT}x24", "-ac"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    env = os.environ.copy()
    env["DISPLAY"] = disp
    env["XAUTHORITY"] = str(root / "empty.Xauthority")
    (root / "empty.Xauthority").touch(exist_ok=True)
    # App must outlive controller; controller runtime is bounded by fixed decisions.
    app_duration = decisions * (planner_wait_s + 0.085 + 0.04) + 0.9 + APP_TAIL_S
    try:
        time.sleep(0.10)
        app = subprocess.Popen([sys.executable, __file__, "--app", str(out), "--app-duration", str(app_duration)], env=env)
        time.sleep(0.18)
        cp = subprocess.run([
            sys.executable, __file__, "--controller", str(out), "--mode", mode,
            "--decisions", str(decisions), "--planner-wait", str(planner_wait_s), "--cover-budget", str(cover_budget_s), "--deadband", str(deadband_abs),
        ], env=env, capture_output=True, text=True, timeout=app_duration + 5)
        if cp.returncode != 0:
            raise RuntimeError(f"controller failed: {cp.stderr}")
        app.wait(timeout=app_duration + 3)
        return audit_arm(out)
    finally:
        xvfb.terminate()
        try:
            xvfb.wait(timeout=1)
        except Exception:
            xvfb.kill()


def run_experiment(root: Path, pairs: int, decisions: int, planner_wait_s: float, cover_budget_s: float, deadband_abs: float) -> dict:
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    orders = [("coast", "recovery"), ("recovery", "coast")]
    all_pairs: list[dict] = []
    for pair in range(pairs):
        result = {}
        order = orders[pair % 2]
        for idx, mode in enumerate(order):
            result[mode] = run_arm(root, pair, mode, idx, decisions, planner_wait_s, cover_budget_s, deadband_abs, 100 + pair * 2 + idx)
        all_pairs.append(result)
        print("PAIR", pair, json.dumps(result, sort_keys=True), flush=True)

    unsafe_delta = [p["recovery"]["unsafe_ms"] - p["coast"]["unsafe_ms"] for p in all_pairs]
    center_delta = [p["recovery"]["center_ms"] - p["coast"]["center_ms"] for p in all_pairs]
    guard_lat = [x for p in all_pairs for x in p["recovery"]["guard_to_app_release_ms"]]
    summary = {
        "schema": "container-x11-typed-deadband-postcondition-successor-v1",
        "claim_scope": "container X11 mechanics only; fixed simulated planner wait; not a model or DOOM efficacy claim",
        "pairs": pairs,
        "decisions_per_arm": decisions,
        "planner_wait_s": planner_wait_s,
        "cover_budget_s": cover_budget_s,\n        "deadband_abs": deadband_abs,
        "pair_results": all_pairs,
        "paired_recovery_minus_coast": {
            "unsafe_ms": unsafe_delta,
            "unsafe_ms_median": statistics.median(unsafe_delta),
            "center_ms": center_delta,
            "center_ms_median": statistics.median(center_delta),
        },
        "safety": {
            "all_terminal_empty": all(p[m]["terminal_empty"] for p in all_pairs for m in ("coast", "recovery")),
            "all_key_events_balanced": all(p[m]["balanced_app_key_events"] for p in all_pairs for m in ("coast", "recovery")),
            "stale_repress_total": sum(p["recovery"]["stale_repress_before_planner"] for p in all_pairs),
            "guard_event_total": sum(p["recovery"]["guard_events"] for p in all_pairs),
            "guard_to_app_release_ms": guard_lat,
            "guard_to_app_release_ms_median": statistics.median(guard_lat) if guard_lat else None,
            "guard_to_app_release_ms_max": max(guard_lat) if guard_lat else None,
            "visual_decoder_error_max": max(p[m]["visual_decoder_error_max"] for p in all_pairs for m in ("coast", "recovery")),
        },
    }
    summary["formal_mechanics_pass"] = bool(
        summary["safety"]["all_terminal_empty"]
        and summary["safety"]["all_key_events_balanced"]
        and summary["safety"]["stale_repress_total"] == 0
        and summary["safety"]["guard_event_total"] >= 1
        and summary["safety"]["guard_to_app_release_ms_max"] is not None
        and summary["safety"]["guard_to_app_release_ms_max"] < 5.0
        and summary["safety"]["visual_decoder_error_max"] < 0.03
        and all(d < 0 for d in unsafe_delta)
    )
    # Hash raw streams to bind the summarized first result.
    summary["raw_sha256"] = {
        str(p.relative_to(root)): sha256_file(p)
        for p in sorted(root.rglob("*.jsonl"))
    }
    (root / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--app")
    ap.add_argument("--app-duration", type=float, default=4.0)
    ap.add_argument("--controller")
    ap.add_argument("--mode", choices=["coast", "recovery"])
    ap.add_argument("--decisions", type=int, default=6)
    ap.add_argument("--planner-wait", type=float, default=0.34)
    ap.add_argument("--cover-budget", type=float, default=0.24)\n    ap.add_argument("--deadband", type=float, default=0.06)
    ap.add_argument("--pairs", type=int, default=3)
    ap.add_argument("--out", default="/tmp/container-x11-bounded-recovery-v3")
    a = ap.parse_args()
    if a.app:
        TaskApp(Path(a.app), a.app_duration).run()
        return
    if a.controller:
        controller(Path(a.controller), a.mode, a.decisions, a.planner_wait, a.cover_budget, a.deadband)
        return
    summary = run_experiment(Path(a.out), a.pairs, a.decisions, a.planner_wait, a.cover_budget, a.deadband)
    print(json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(0 if summary["formal_mechanics_pass"] else 2)


if __name__ == "__main__":
    main()
