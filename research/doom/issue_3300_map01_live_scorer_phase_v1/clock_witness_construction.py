"""Excluded test of passive async-clock progress under the normal MAP01 setup."""
from __future__ import annotations

import json
import hashlib
import subprocess
import sys
import time
from pathlib import Path

import vizdoom as vd

sys.path.insert(0, "/opt/phase-probe")
import runner as phase_runner


OUT = Path("/results")
WAD = "/assets/freedoom2.wad"
rows = []

for repetition in range(3):
    game = vd.DoomGame()
    observed = phase_runner.ObservedGame(game)
    row = {"repetition": repetition, "setup": "not_started", "samples": []}
    try:
        game.set_doom_game_path(WAD)
        game.set_doom_scenario_path("")
        game.set_doom_map("MAP01")
        game.set_mode(vd.Mode.ASYNC_SPECTATOR)
        game.set_ticrate(35)
        game.set_seed(345300 + repetition)
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
        row["buttons_readback"] = [str(button) for button in game.get_available_buttons()]
        window_ids = subprocess.check_output(
            ["xdotool", "search", "--onlyvisible", "--name", "VIZDOOM"], text=True
        ).splitlines()
        if len(window_ids) != 1:
            raise RuntimeError(f"expected one visible ViZDoom window, found {window_ids!r}")
        subprocess.run(["xdotool", "windowactivate", "--sync", window_ids[0]], check=True)
        row["focused_window_id"] = window_ids[0]
        # One initial refresh mirrors the existing ordinary-speed MAP01 harness.
        # No advancement call occurs between the timed read checkpoints below.
        time.sleep(0.3)
        game.advance_action(1, True)
        start_ns = time.perf_counter_ns()
        before = int(game.get_episode_time())
        for delay_ms in (250, 500, 1000, 2000):
            time.sleep(max(0.0, (delay_ms - (time.perf_counter_ns() - start_ns) / 1e6) / 1000))
            sampled_ns = time.perf_counter_ns()
            tic = int(game.get_episode_time())
            state_start_ns = time.perf_counter_ns()
            state = game.get_state()
            state_end_ns = time.perf_counter_ns()
            frame_path = OUT / f"frame-r{repetition}-{delay_ms}ms.xwd"
            frame_start_ns = time.perf_counter_ns()
            subprocess.run(["xwd", "-silent", "-id", window_ids[0], "-out", str(frame_path)], check=True)
            frame_end_ns = time.perf_counter_ns()
            row["samples"].append({
                "elapsed_ns": sampled_ns - start_ns,
                "tic": tic,
                "state_tic": None if state is None else int(state.tic),
                "state_read_span_ns": state_end_ns - state_start_ns,
                "screen_sha256": None if state is None or state.screen_buffer is None
                else hashlib.sha256(state.screen_buffer.tobytes()).hexdigest(),
                "x11_frame_sha256": hashlib.sha256(frame_path.read_bytes()).hexdigest(),
                "x11_frame_bytes": frame_path.stat().st_size,
                "x11_frame_start_ns": frame_start_ns,
                "x11_frame_end_ns": frame_end_ns,
            })
        row["before_tic"] = before
        row["after_tic"] = row["samples"][-1]["tic"]
        row["elapsed_ns"] = row["samples"][-1]["elapsed_ns"]
        row["estimated_hz"] = (row["after_tic"] - before) * 1e9 / row["elapsed_ns"]
        row["passive_interval_advance_calls"] = 0
        observed.role.name = "exact_scorer_predicate"
        scorer_start_ns = time.perf_counter_ns()
        try:
            scorer_result = phase_runner._coherent_progress_sample(
                observed, vd.GameVariable, 600
            )
            row["scorer_status"] = "returned"
            row["scorer_return"] = scorer_result.as_dict()
        except BaseException as exc:
            row["scorer_status"] = "raised"
            row["scorer_error"] = {"type": type(exc).__name__, "message": str(exc)}
        row["scorer_start_ns"] = scorer_start_ns
        row["scorer_end_ns"] = time.perf_counter_ns()
        row["scorer_api_trace"] = observed.trace
        refresh_start_ns = time.perf_counter_ns()
        game.advance_action(0, True)
        refresh_end_ns = time.perf_counter_ns()
        refreshed_frame_path = OUT / f"frame-r{repetition}-post-refresh.xwd"
        subprocess.run(["xwd", "-silent", "-id", window_ids[0], "-out", str(refreshed_frame_path)], check=True)
        row["post_interval_refresh"] = {
            "tic": int(game.get_episode_time()),
            "start_ns": refresh_start_ns,
            "end_ns": refresh_end_ns,
            "span_ns": refresh_end_ns - refresh_start_ns,
            "x11_frame_sha256": hashlib.sha256(refreshed_frame_path.read_bytes()).hexdigest(),
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
