"""No-display, no-action ASYNC_SPECTATOR MAP01 clock-liveness probe."""
from __future__ import annotations

import hashlib
import json
import platform
import sys
import time
from pathlib import Path

import vizdoom as vd

sys.path.insert(0, "/opt/phase-probe")
import runner as phase_runner

OUT = Path("/results")
WAD = Path(vd.__file__).parent / "freedoom2.wad"
rows = []

for repetition in range(3):
    game = vd.DoomGame()
    observed = phase_runner.ObservedGame(game)
    row = {
        "repetition": repetition,
        "setup": "not_started",
        "samples": [],
        "vizdoom_version": getattr(vd, "__version__", "unknown"),
        "python_version": sys.version,
        "architecture": platform.machine(),
    }
    try:
        row["wad_sha256"] = hashlib.sha256(WAD.read_bytes()).hexdigest()
        game.set_doom_game_path(str(WAD))
        game.set_doom_scenario_path("")
        game.set_doom_map("MAP01")
        game.set_mode(vd.Mode.ASYNC_SPECTATOR)
        game.set_ticrate(35)
        game.set_seed(345322 + repetition)
        game.set_episode_timeout(35 * 60)
        game.set_window_visible(False)
        game.set_console_enabled(False)
        game.set_sound_enabled(False)
        game.set_screen_resolution(vd.ScreenResolution.RES_640X480)
        game.set_available_buttons([
            vd.Button.TURN_LEFT, vd.Button.TURN_RIGHT,
            vd.Button.MOVE_FORWARD, vd.Button.MOVE_BACKWARD,
            vd.Button.MOVE_LEFT, vd.Button.MOVE_RIGHT,
            vd.Button.ATTACK, vd.Button.USE, vd.Button.SPEED,
        ])
        game.init()
        row["setup"] = "initialized"
        row["mode_readback"] = str(game.get_mode())
        row["ticrate_readback"] = game.get_ticrate()
        row["window_visible_configured"] = False
        start_ns = time.perf_counter_ns()
        deadline_ns = start_ns + 2_000_000_000
        while time.perf_counter_ns() < deadline_ns:
            read_start_ns = time.perf_counter_ns()
            episode_tic = int(game.get_episode_time())
            game_state = game.get_state()
            server_state = game.get_server_state()
            read_end_ns = time.perf_counter_ns()
            row["samples"].append({
                "sample_start_ns": read_start_ns,
                "sample_end_ns": read_end_ns,
                "get_episode_time": episode_tic,
                "game_state_tic": None if game_state is None else int(game_state.tic),
                "game_state_number": None if game_state is None else int(game_state.number),
                "server_state_tic": None if server_state is None else int(server_state.tic),
            })
            time.sleep(0.01)
        row["passive_elapsed_ns"] = time.perf_counter_ns() - start_ns
        row["advancing_api_calls"] = {"advance_action": 0, "make_action": 0, "set_action": 0}
        observed.role.name = "exact_scorer_predicate"
        scorer_start_ns = time.perf_counter_ns()
        try:
            sample = phase_runner._coherent_progress_sample(observed, vd.GameVariable, 600)
            row["scorer_status"] = "returned"
            row["scorer_return"] = sample.as_dict()
        except BaseException as exc:
            row["scorer_status"] = "raised"
            row["scorer_error"] = {"type": type(exc).__name__, "message": str(exc)}
        row["scorer_start_ns"] = scorer_start_ns
        row["scorer_end_ns"] = time.perf_counter_ns()
        row["scorer_api_trace"] = observed.trace
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
print(json.dumps(rows, sort_keys=True))
