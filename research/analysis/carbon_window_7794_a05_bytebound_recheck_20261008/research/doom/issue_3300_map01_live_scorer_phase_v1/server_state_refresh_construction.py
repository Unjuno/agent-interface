"""Construction-only comparison of passive ServerState and action refresh."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import vizdoom as vd

OUT = Path("/results")
WAD = Path(vd.__file__).parent / "freedoom2.wad"
rows = []


def snapshot(game):
    start = time.perf_counter_ns()
    server = game.get_server_state()
    server_end = time.perf_counter_ns()
    episode = int(game.get_episode_time())
    state = game.get_state()
    return {
        "read_start_ns": start,
        "server_state_tic": int(server.tic),
        "server_state_call_end_ns": server_end,
        "server_state_span_ns": server_end - start,
        "game_episode_tic": episode,
        "game_state_tic": None if state is None else int(state.tic),
        "game_state_number": None if state is None else int(state.number),
    }


for repetition in range(3):
    game = vd.DoomGame()
    row = {"repetition": repetition, "setup": "not_started"}
    try:
        row["wad_sha256"] = hashlib.sha256(WAD.read_bytes()).hexdigest()
        game.set_doom_game_path(str(WAD))
        game.set_doom_scenario_path("")
        game.set_doom_map("MAP01")
        game.set_mode(vd.Mode.ASYNC_SPECTATOR)
        game.set_ticrate(35)
        game.set_seed(345321 + repetition)
        game.set_episode_timeout(35 * 60)
        game.set_window_visible(True)
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
        row["initial"] = snapshot(game)
        passive_start_ns = time.perf_counter_ns()
        time.sleep(2.0)
        row["passive_elapsed_ns"] = time.perf_counter_ns() - passive_start_ns
        row["passive_end"] = snapshot(game)
        action_start_ns = time.perf_counter_ns()
        game.advance_action(1, True)
        action_end_ns = time.perf_counter_ns()
        row["action_refresh"] = {
            "start_ns": action_start_ns,
            "end_ns": action_end_ns,
            "span_ns": action_end_ns - action_start_ns,
            "snapshot": snapshot(game),
        }
        row["calls_during_passive_interval"] = {
            "advance_action": 0,
            "make_action": 0,
            "set_action": 0,
        }
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
