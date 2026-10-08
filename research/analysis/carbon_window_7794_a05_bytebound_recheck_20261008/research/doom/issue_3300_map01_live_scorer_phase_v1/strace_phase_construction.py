"""Construction probe pairing exact scorer traces with engine write timestamps."""
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
if hashlib.sha256(WAD.read_bytes()).hexdigest() != EXPECTED_WAD:
    raise SystemExit("STOP: official WAD hash mismatch")


def clock_anchor() -> dict[str, int]:
    wall_before = time.time_ns()
    monotonic = time.monotonic_ns()
    wall_after = time.time_ns()
    return {
        "wall_before_ns": wall_before,
        "monotonic_ns": monotonic,
        "wall_after_ns": wall_after,
    }


rows = []
for repetition in range(3):
    game = vd.DoomGame()
    row = {"repetition": repetition, "setup": "not_started", "anchors": []}
    try:
        game.set_doom_game_path(str(WAD))
        game.set_doom_scenario_path("")
        game.set_doom_map("MAP01")
        game.set_mode(vd.Mode.ASYNC_SPECTATOR)
        game.set_ticrate(35)
        game.set_seed(345371 + repetition)
        game.set_episode_timeout(35 * 60)
        game.set_window_visible(False)
        game.set_console_enabled(False)
        game.set_sound_enabled(False)
        game.set_available_buttons([])
        game.set_game_args("+viz_debug 2")
        game.init()
        game.new_episode()
        row.update(
            setup="initialized",
            mode=str(game.get_mode()),
            ticrate=game.get_ticrate(),
            initial_api_tic=int(game.get_episode_time()),
            wad_sha256=hashlib.sha256(WAD.read_bytes()).hexdigest(),
            vizdoom_version=getattr(vd, "__version__", "unknown"),
        )
        row["anchors"].append(clock_anchor())
        print("PHASE_EVENT " + json.dumps({
            "kind": "passive_begin", "repetition": repetition,
            **clock_anchor(),
        }, sort_keys=True), flush=True)
        start_mono = time.monotonic_ns()
        deadline = start_mono + 1_500_000_000
        samples = []
        while time.monotonic_ns() < deadline:
            a = time.monotonic_ns()
            tic = int(game.get_episode_time())
            b = time.monotonic_ns()
            samples.append({"start_ns": a, "end_ns": b, "api_tic": tic})
            row["anchors"].append(clock_anchor())
            time.sleep(0.05)
        row["passive_start_monotonic_ns"] = start_mono
        row["passive_end_monotonic_ns"] = time.monotonic_ns()
        row["samples"] = samples
        row["final_api_tic"] = int(game.get_episode_time())
        observed = phase_runner.ObservedGame(game)
        observed.role.name = "exact_scorer_predicate"
        row["scorer_call_start_anchor"] = clock_anchor()
        row["scorer_start_monotonic_ns"] = time.monotonic_ns()
        try:
            sample = phase_runner._coherent_progress_sample(
                observed, vd.GameVariable, 600
            )
            row["scorer_status"] = "returned"
            row["scorer_return"] = sample.as_dict()
        except BaseException as exc:
            row["scorer_status"] = "raised"
            row["scorer_error"] = {"type": type(exc).__name__, "message": str(exc)}
        row["scorer_end_monotonic_ns"] = time.monotonic_ns()
        row["scorer_call_end_anchor"] = clock_anchor()
        row["scorer_api_trace"] = observed.trace
        row["advancing_api_calls"] = 0
        row["elapsed_ns"] = row["passive_end_monotonic_ns"] - start_mono
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
print("PHASE_SUMMARY " + json.dumps([
    {"repetition": r["repetition"], "setup": r["setup"],
     "scorer_status": r.get("scorer_status"), "closed": r.get("closed"),
     "api_tic": r.get("final_api_tic"), "samples": len(r.get("samples", []))}
    for r in rows
], sort_keys=True), flush=True)
