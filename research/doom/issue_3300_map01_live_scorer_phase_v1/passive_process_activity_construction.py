"""Excluded 1.3.0 process-activity check during passive MAP01 waits."""
from __future__ import annotations

import glob
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path

import vizdoom as vd

sys.path.insert(0, "/opt/phase-probe")
import runner as phase_runner

OUT = Path("/results")
WAD = Path("/assets/freedoom2.wad")
EXPECTED_WAD = "a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b"


def proc_rows():
    rows = {}
    for path in glob.glob("/proc/[0-9]*/stat"):
        try:
            raw = Path(path).read_text()
            # comm may contain spaces and parentheses; split after its final ')'.
            pid_text, rest = raw.split("(", 1)
            comm, tail = rest.rsplit(")", 1)
            fields = tail.split()
            pid = int(pid_text.strip())
            rows[pid] = {
                "pid": pid,
                "comm": comm,
                "state": fields[0],
                "ppid": int(fields[1]),
                "utime_ticks": int(fields[11]),
                "stime_ticks": int(fields[12]),
            }
        except (OSError, ValueError, IndexError):
            continue
    return rows


if hashlib.sha256(WAD.read_bytes()).hexdigest() != EXPECTED_WAD:
    raise SystemExit("STOP: official WAD hash mismatch")
rows = []
for repetition in range(3):
    game = vd.DoomGame()
    row = {"repetition": repetition, "setup": "not_started", "samples": []}
    try:
        row["wad_sha256"] = hashlib.sha256(WAD.read_bytes()).hexdigest()
        row["vizdoom_version"] = getattr(vd, "__version__", "unknown")
        game.set_doom_game_path(str(WAD))
        game.set_doom_scenario_path("")
        game.set_doom_map("MAP01")
        game.set_mode(vd.Mode.ASYNC_SPECTATOR)
        game.set_ticrate(35)
        game.set_seed(345331 + repetition)
        game.set_episode_timeout(35 * 60)
        game.set_window_visible(False)
        game.set_console_enabled(False)
        game.set_sound_enabled(False)
        game.set_available_buttons([])
        game.init()
        game.new_episode()
        row.update(
            setup="initialized",
            platform=platform.platform(),
            architecture=platform.machine(),
            python_version=sys.version,
            process_clk_tck=os.sysconf("SC_CLK_TCK"),
            mode_readback=str(game.get_mode()),
            ticrate_readback=game.get_ticrate(),
            initial_tic=int(game.get_episode_time()),
            configured_window_visible=False,
            available_buttons_readback=list(game.get_available_buttons()),
            advancing_api_calls=0,
        )
        start_ns = time.monotonic_ns()
        deadline_ns = start_ns + 1_500_000_000
        start_procs = proc_rows()
        while time.monotonic_ns() < deadline_ns:
            read_start = time.monotonic_ns()
            tic = int(game.get_episode_time())
            read_end = time.monotonic_ns()
            procs = proc_rows()
            children = [p for p in procs.values() if p["ppid"] == os.getpid()]
            row["samples"].append({
                "read_start_ns": read_start,
                "read_end_ns": read_end,
                "tic": tic,
                "children": children,
            })
            time.sleep(0.05)
        end_ns = time.monotonic_ns()
        end_procs = proc_rows()
        child_deltas = []
        for pid, final in end_procs.items():
            initial = start_procs.get(pid)
            if initial and final["ppid"] == os.getpid():
                child_deltas.append({
                    "pid": pid,
                    "comm": final["comm"],
                    "start_state": initial["state"],
                    "end_state": final["state"],
                    "cpu_ticks_delta": (final["utime_ticks"] + final["stime_ticks"]
                                        - initial["utime_ticks"] - initial["stime_ticks"]),
                })
        row["elapsed_ns"] = end_ns - start_ns
        row["final_tic"] = int(game.get_episode_time())
        row["clock_progress_observed"] = row["final_tic"] > row["initial_tic"]
        row["child_cpu_deltas"] = child_deltas
        observed = phase_runner.ObservedGame(game)
        observed.role.name = "exact_scorer_predicate"
        scorer_start = time.monotonic_ns()
        try:
            sample = phase_runner._coherent_progress_sample(
                observed, vd.GameVariable, 600
            )
            row["scorer_status"] = "returned"
            row["scorer_return"] = sample.as_dict()
        except BaseException as exc:
            row["scorer_status"] = "raised"
            row["scorer_error"] = {
                "type": type(exc).__name__, "message": str(exc)
            }
        row["scorer_start_ns"] = scorer_start
        row["scorer_end_ns"] = time.monotonic_ns()
        row["scorer_api_trace"] = observed.trace
        row["scorer_call_span_ns"] = row["scorer_end_ns"] - row["scorer_start_ns"]
    except BaseException as exc:
        row["error"] = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        try:
            game.close()
            row["closed"] = True
        except BaseException as exc:
            row["closed"] = False
            row["close_error"] = {"type": type(exc).__name__, "message": str(exc)}
        rows.append(row)

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "raw.json").write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n")
print(json.dumps([
    {
        "repetition": r["repetition"],
        "setup": r["setup"],
        "samples": len(r.get("samples", [])),
        "tics": sorted({s["tic"] for s in r.get("samples", [])}),
        "elapsed_ns": r.get("elapsed_ns"),
        "child_cpu_deltas": r.get("child_cpu_deltas"),
        "scorer_status": r.get("scorer_status"),
        "clock_progress_observed": r.get("clock_progress_observed"),
        "closed": r.get("closed"),
    }
    for r in rows
], sort_keys=True))
