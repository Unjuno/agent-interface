"""Clock-domain calibration probe using timestamped Docker VIZ_Tic logs."""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import vizdoom as vd

sys.path.insert(0, "/opt/phase-probe")
import runner as phase_runner

OUT = Path("/results")
WAD = Path("/assets/freedoom2.wad")
EXPECTED_WAD = "a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b"
OFFSETS_NS = [0, 4_761_905, 9_523_810, 14_285_714, 19_047_619, 23_809_524]
if hashlib.sha256(WAD.read_bytes()).hexdigest() != EXPECTED_WAD:
    raise SystemExit("STOP: official WAD hash mismatch")


def event(kind: str, **values: object) -> None:
    print("RUN33_EVENT " + json.dumps({
        "kind": kind,
        "wall_ns": time.time_ns(),
        "monotonic_ns": time.monotonic_ns(),
        **values,
    }, sort_keys=True), flush=True)


rows = []
for repetition, offset_ns in enumerate(OFFSETS_NS):
    game = vd.DoomGame()
    row = {"repetition": repetition, "phase_offset_target_ns": offset_ns, "setup": "not_started"}
    try:
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
        game.set_game_args("+viz_debug 2")
        row.update(
            wad_sha256=hashlib.sha256(WAD.read_bytes()).hexdigest(),
            vizdoom_version=getattr(vd, "__version__", "unknown"),
            instrumentation="VIZ_Tic debug level 2; Docker timestamped stdout; stdbuf -oL",
        )
        game.init()
        game.new_episode()
        row.update(setup="initialized", mode_readback=str(game.get_mode()),
                   ticrate_readback=game.get_ticrate(),
                   initial_api_tic=int(game.get_episode_time()),
                   game_args=game.get_game_args())
        event("passive_begin", repetition=repetition, target_offset_ns=offset_ns)
        start_mono = time.monotonic_ns()
        target = start_mono + offset_ns
        while time.monotonic_ns() < target:
            time.sleep(min(0.001, (target - time.monotonic_ns()) / 1e9))
        call_wall_start = time.time_ns()
        call_mono_start = time.monotonic_ns()
        event("scorer_begin", repetition=repetition,
              call_wall_ns=call_wall_start, call_monotonic_ns=call_mono_start)
        observed = phase_runner.ObservedGame(game)
        observed.role.name = "exact_scorer_predicate"
        try:
            sample = phase_runner._coherent_progress_sample(
                observed, vd.GameVariable, 600
            )
            row["scorer_status"] = "returned"
            row["scorer_return"] = sample.as_dict()
        except BaseException as exc:
            row["scorer_status"] = "raised"
            row["scorer_error"] = {"type": type(exc).__name__, "message": str(exc)}
        call_mono_end = time.monotonic_ns()
        call_wall_end = time.time_ns()
        event("scorer_end", repetition=repetition,
              call_wall_ns=call_wall_end, call_monotonic_ns=call_mono_end)
        row.update(call_wall_start_ns=call_wall_start,
                   call_monotonic_start_ns=call_mono_start,
                   call_wall_end_ns=call_wall_end,
                   call_monotonic_end_ns=call_mono_end,
                   scorer_api_trace=observed.trace,
                   api_tic_after=int(game.get_episode_time()),
                   advancing_api_calls=0)
        time.sleep(0.1)
        row["final_api_tic"] = int(game.get_episode_time())
        event("passive_end", repetition=repetition,
              final_api_tic=row["final_api_tic"])
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
print("RUN33_SUMMARY " + json.dumps([
    {"repetition": r["repetition"], "offset_target_ns": r["phase_offset_target_ns"],
     "mode": r.get("mode_readback"), "tic_before": r.get("initial_api_tic"),
     "tic_after": r.get("final_api_tic"), "scorer_status": r.get("scorer_status"),
     "closed": r.get("closed")}
    for r in rows
], sort_keys=True), flush=True)
