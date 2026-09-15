#!/usr/bin/env python3
"""Held-out container/X11 transfer test for bounded recovery.

Formal schedules are frozen in this file and must not be executed before the
matching preregistration is published. This module reuses the retained v3
controller/auditor without mutating it.
"""
from __future__ import annotations
import argparse, hashlib, json, os, statistics, subprocess, sys, time
from pathlib import Path
import container_x11_bounded_recovery_v3 as base

SCHEDULES = {
    "late_flip": [(0.95, 0.40), (1.65, -0.58), (99.0, 0.32)],
    "early_flip": [(0.62, 0.48), (1.28, -0.62), (99.0, 0.38)],
    "double_flip": [(0.55, 0.46), (1.02, -0.70), (1.52, 0.62), (99.0, -0.28)],
    "fast_drift": [(0.80, 0.67), (1.40, -0.76), (99.0, 0.55)],
}
FORMAL_ORDER = ["late_flip", "early_flip", "double_flip", "fast_drift"]


class TransferTaskApp(base.TaskApp):
    def __init__(self, out: Path, duration: float, schedule: str):
        if schedule not in SCHEDULES:
            raise ValueError(f"unknown schedule: {schedule}")
        self.schedule = schedule
        super().__init__(out, duration)

    def drift(self, t_s: float) -> float:
        for until_s, value in SCHEDULES[self.schedule]:
            if t_s < until_s:
                return value
        raise AssertionError("schedule must have terminal segment")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_arm(root: Path, pair: int, schedule: str, mode: str, order_index: int,
            decisions: int, planner_wait_s: float, cover_budget_s: float,
            display_num: int) -> dict:
    out = root / f"pair-{pair:02d}-{schedule}-{order_index}-{mode}"
    disp = f":{display_num}"
    xvfb = subprocess.Popen(
        ["Xvfb", disp, "-screen", "0", f"{base.WIDTH}x{base.HEIGHT}x24", "-ac"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    env = os.environ.copy()
    env["DISPLAY"] = disp
    env["XAUTHORITY"] = str(root / "empty.Xauthority")
    (root / "empty.Xauthority").touch(exist_ok=True)
    app_duration = decisions * (planner_wait_s + 0.085 + 0.04) + 0.9 + base.APP_TAIL_S
    try:
        time.sleep(0.10)
        app = subprocess.Popen(
            [sys.executable, __file__, "--app", str(out), "--app-duration", str(app_duration), "--schedule", schedule],
            env=env,
        )
        time.sleep(0.18)
        cp = subprocess.run(
            [sys.executable, __file__, "--controller", str(out), "--mode", mode,
             "--decisions", str(decisions), "--planner-wait", str(planner_wait_s),
             "--cover-budget", str(cover_budget_s)],
            env=env, capture_output=True, text=True, timeout=app_duration + 5,
        )
        if cp.returncode != 0:
            raise RuntimeError(f"controller failed: {cp.stderr}")
        app.wait(timeout=app_duration + 3)
        result = base.audit_arm(out)
        result["schedule"] = schedule
        return result
    finally:
        xvfb.terminate()
        try:
            xvfb.wait(timeout=1)
        except Exception:
            xvfb.kill()


def run_formal(root: Path, decisions: int, planner_wait_s: float, cover_budget_s: float) -> dict:
    if root.exists():
        raise FileExistsError(f"formal output already exists: {root}")
    root.mkdir(parents=True)
    orders = [("coast", "recovery"), ("recovery", "coast")]
    pairs = []
    for pair, schedule in enumerate(FORMAL_ORDER):
        order = orders[pair % 2]
        result = {"schedule": schedule}
        for idx, mode in enumerate(order):
            result[mode] = run_arm(
                root, pair, schedule, mode, idx, decisions, planner_wait_s,
                cover_budget_s, 130 + pair * 2 + idx,
            )
        pairs.append(result)
        print("PAIR", pair, json.dumps(result, sort_keys=True), flush=True)

    deltas = [p["recovery"]["unsafe_ms"] - p["coast"]["unsafe_ms"] for p in pairs]
    center_deltas = [p["recovery"]["center_ms"] - p["coast"]["center_ms"] for p in pairs]
    guard_lat = [x for p in pairs for x in p["recovery"]["guard_to_app_release_ms"]]
    wins = sum(1 for d in deltas if d <= 0)
    safety = {
        "all_terminal_empty": all(p[m]["terminal_empty"] for p in pairs for m in ("coast", "recovery")),
        "all_key_events_balanced": all(p[m]["balanced_app_key_events"] for p in pairs for m in ("coast", "recovery")),
        "stale_repress_total": sum(p["recovery"]["stale_repress_before_planner"] for p in pairs),
        "guard_event_total": sum(p["recovery"]["guard_events"] for p in pairs),
        "guard_to_app_release_ms": guard_lat,
        "guard_to_app_release_ms_max": max(guard_lat) if guard_lat else None,
        "visual_decoder_error_max": max(p[m]["visual_decoder_error_max"] for p in pairs for m in ("coast", "recovery")),
    }
    safety_pass = bool(
        safety["all_terminal_empty"]
        and safety["all_key_events_balanced"]
        and safety["stale_repress_total"] == 0
        and safety["visual_decoder_error_max"] < 0.03
        and (safety["guard_to_app_release_ms_max"] is None or safety["guard_to_app_release_ms_max"] < 5.0)
    )
    guard_exposure_sufficient = safety["guard_event_total"] >= 2
    efficacy_pass = bool(
        wins >= 3
        and statistics.median(deltas) < 0
        and max(deltas) <= 100.0
    )
    if not safety_pass:
        disposition = "FAIL_SAFETY"
    elif not guard_exposure_sufficient:
        disposition = "UNCERTAIN_GUARD_EXPOSURE"
    elif efficacy_pass:
        disposition = "PASS_TRANSFER"
    else:
        disposition = "HOLD_NO_TRANSFER"

    summary = {
        "schema": "container-x11-bounded-recovery-transfer-v2",
        "claim_scope": "held-out container X11 dynamics only; no model/DOOM/general speed claim",
        "formal_schedule_order": FORMAL_ORDER,
        "schedule_definitions": SCHEDULES,
        "decisions_per_arm": decisions,
        "planner_wait_s": planner_wait_s,
        "cover_budget_s": cover_budget_s,
        "pair_results": pairs,
        "paired_recovery_minus_coast": {
            "unsafe_ms": deltas,
            "unsafe_ms_median": statistics.median(deltas),
            "center_ms": center_deltas,
            "center_ms_median": statistics.median(center_deltas),
            "nonworse_count": wins,
        },
        "safety": safety,
        "formal_safety_pass": safety_pass,
        "guard_exposure_sufficient": guard_exposure_sufficient,
        "formal_efficacy_pass": efficacy_pass,
        "disposition": disposition,
        "raw_sha256": {str(p.relative_to(root)): sha256_file(p) for p in sorted(root.rglob("*.jsonl"))},
    }
    (root / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--app")
    ap.add_argument("--app-duration", type=float, default=4.0)
    ap.add_argument("--schedule", choices=sorted(SCHEDULES))
    ap.add_argument("--controller")
    ap.add_argument("--mode", choices=["coast", "recovery"])
    ap.add_argument("--decisions", type=int, default=6)
    ap.add_argument("--planner-wait", type=float, default=0.34)
    ap.add_argument("--cover-budget", type=float, default=0.24)
    ap.add_argument("--out", default="/tmp/container-x11-bounded-recovery-transfer-v2")
    a = ap.parse_args()
    if a.app:
        if not a.schedule:
            raise SystemExit("--schedule required with --app")
        TransferTaskApp(Path(a.app), a.app_duration, a.schedule).run()
        return
    if a.controller:
        base.controller(Path(a.controller), a.mode, a.decisions, a.planner_wait, a.cover_budget)
        return
    summary = run_formal(Path(a.out), a.decisions, a.planner_wait, a.cover_budget)
    print(json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(0 if summary["disposition"] == "PASS_TRANSFER" else 2)


if __name__ == "__main__":
    main()
