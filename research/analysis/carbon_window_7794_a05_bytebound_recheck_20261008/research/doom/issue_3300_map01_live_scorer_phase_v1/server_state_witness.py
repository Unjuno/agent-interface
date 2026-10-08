"""Excluded read-only test of ViZDoom ServerState tic as an independent witness."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import vizdoom as vd

OUT = Path("/results")
WAD = Path(vd.__file__).parent / "freedoom2.wad"
rows = []

for repetition in range(3):
    game = vd.DoomGame()
    row = {"repetition": repetition, "setup": "not_started", "samples": []}
    try:
        row["wad_sha256"] = hashlib.sha256(WAD.read_bytes()).hexdigest()
        game.set_doom_game_path(str(WAD))
        game.set_doom_scenario_path("")
        game.set_doom_map("MAP01")
        game.set_mode(vd.Mode.ASYNC_SPECTATOR)
        game.set_ticrate(35)
        game.set_seed(345318 + repetition)
        game.set_episode_timeout(35 * 60)
        game.set_window_visible(True)
        game.set_console_enabled(False)
        game.set_sound_enabled(False)
        game.set_screen_resolution(vd.ScreenResolution.RES_640X480)
        game.set_render_hud(True)
        game.set_render_crosshair(True)
        game.set_render_all_frames(True)
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
        start_ns = time.perf_counter_ns()
        deadline_ns = start_ns + 2_000_000_000
        while time.perf_counter_ns() < deadline_ns:
            call_start_ns = time.perf_counter_ns()
            try:
                server = game.get_server_state()
                server_error = None
            except BaseException as exc:
                server, server_error = None, {"type": type(exc).__name__, "message": str(exc)}
            server_end_ns = time.perf_counter_ns()
            try:
                game_tic = int(game.get_episode_time())
            except BaseException as exc:
                game_tic = None
                game_error = {"type": type(exc).__name__, "message": str(exc)}
            else:
                game_error = None
            state = game.get_state()
            row["samples"].append({
                "sample_start_ns": call_start_ns,
                "server_state_tic": None if server is None else int(server.tic),
                "server_state_type": None if server is None else type(server).__name__,
                "server_state_error": server_error,
                "server_state_fields": None if server is None else {
                    "player_count": int(server.player_count),
                    "players_in_game": list(server.players_in_game),
                    "players_afk": list(server.players_afk),
                    "players_last_action_tic": list(server.players_last_action_tic),
                },
                "game_episode_tic": game_tic,
                "game_state_tic": None if state is None else int(state.tic),
                "game_episode_error": game_error,
                "call_span_ns": server_end_ns - call_start_ns,
            })
            time.sleep(0.01)
        row["elapsed_ns"] = time.perf_counter_ns() - start_ns
        row["read_only_advance_calls"] = 0
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
