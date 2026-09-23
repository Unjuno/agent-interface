"""Continuously advancing Freedoom MAP01 with X11 observation and OS input."""

import argparse
import contextlib
import hashlib
import json
import os
import shutil
import sys
import threading
import time
from pathlib import Path

import vizdoom as vd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "live_control"))
from executor_v3 import Executor
from lease import Expired
from coast_backend_v1 import Backend, suite


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--skill", type=int, choices=range(1,6), default=1)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    lock = threading.RLock()
    session = game = executor = backend = None
    control_started_ns = None

    def emit(row):
        with lock:
            row["emit_ns"] = time.perf_counter_ns()
            encoded = json.dumps(row)
            with (args.out / "events.jsonl").open("a") as stream:
                stream.write(encoded + "\n")
            with (args.out / "delivered.jsonl").open("a") as stream:
                stream.write(encoded + "\n")
            print(encoded, flush=True)

    sources = {}
    for path in (Path(__file__), HERE.parent / "live_control/session_v8.py",
                 HERE.parent / "live_control/executor_v3.py",
                 HERE.parent / "live_control/lease.py",
                 HERE.parent / "live_control/session_v9.py",
                 HERE.parent / "live_control/session_v9.py",
                 HERE.parent / "live_control/session_v10.py",
                 HERE.parent / "live_control/coast_backend_v1.py"):
        sources[str(path.relative_to(HERE.parent))] = hashlib.sha256(path.read_bytes()).hexdigest()
    (args.out / "sources.json").write_text(json.dumps(sources, indent=2))
    try:
        with (args.out / "setup.txt").open("w") as diagnostics, contextlib.redirect_stdout(diagnostics):
            session = suite.Session()
            atom = session.d.intern_atom("_NET_SUPPORTING_WM_CHECK")
            session._wait(lambda: session.d.screen().root.get_full_property(atom, 0) is not None,
                          4, "WM readiness")
            for key in ("DISPLAY", "XAUTHORITY", "HOME", "XDG_CONFIG_HOME",
                        "XDG_CACHE_HOME", "XDG_RUNTIME_DIR"):
                os.environ[key] = session.env[key]
            os.environ["SDL_VIDEODRIVER"] = "x11"
            os.environ.pop("WAYLAND_DISPLAY", None)
            package = Path(vd.__file__).parent
            iwad = package / "freedoom2.wad"
            config = session.tmp / "doom.ini"
            config.write_text(
                "[Doom.Bindings]\n"
                "leftarrow=+left\nrightarrow=+right\n"
                "uparrow=+forward\ndownarrow=+back\n"
                "w=+forward\ns=+back\na=+moveleft\nd=+moveright\n"
                "e=+use\nenter=+use\nspace=+attack\nctrl=+attack\n"
                "shift=+speed\n", encoding="utf-8")
            game = vd.DoomGame()
            game.set_doom_game_path(str(iwad))
            game.set_doom_scenario_path("")
            game.set_doom_map("MAP01")
            game.set_doom_config_path(str(config))
            game.set_mode(vd.Mode.ASYNC_SPECTATOR)
            game.set_ticrate(35)
            game.set_seed(args.seed)
            game.set_doom_skill(args.skill)
            game.set_episode_timeout(35 * args.timeout_seconds)
            game.set_window_visible(True)
            game.set_console_enabled(False)
            game.set_sound_enabled(False)
            game.set_screen_resolution(vd.ScreenResolution.RES_640X480)
            game.set_render_hud(True)
            game.set_render_crosshair(True)
            game.set_render_all_frames(True)
            game.set_available_buttons([
                vd.Button.TURN_LEFT, vd.Button.TURN_RIGHT, vd.Button.MOVE_FORWARD,
                vd.Button.MOVE_BACKWARD, vd.Button.MOVE_LEFT, vd.Button.MOVE_RIGHT,
                vd.Button.ATTACK, vd.Button.USE, vd.Button.SPEED])
            game.set_available_game_variables([vd.GameVariable.DEATHCOUNT,
                                               vd.GameVariable.KILLCOUNT])
            game.init()
        from PIL import ImageGrab
        time.sleep(0.3)
        windows = session.windows()
        (args.out / "windows.txt").write_text(windows)
        ImageGrab.grab(xdisplay=session.name).save(args.out / "setup-screen.png")
        candidates = [line for line in windows.splitlines() if "doom" in line.lower()]
        if len(candidates) != 1:
            raise RuntimeError("Expected one Doom window: " + repr(windows))
        session.focus(" ".join(candidates[0].split()[3:]))
        game.advance_action(1, True)
        before = game.get_episode_time()
        wall = time.perf_counter()
        time.sleep(2)
        game.advance_action(1, True)
        after = game.get_episode_time()
        elapsed = time.perf_counter() - wall
        iwad = Path(vd.__file__).parent / "freedoom2.wad"
        environment = {"vizdoom": vd.__version__, "mode": str(game.get_mode()),
            "ticrate": game.get_ticrate(), "seed": args.seed, "map": "MAP01", "skill": args.skill,
            "scenario_path": None, "iwad": str(iwad),
            "iwad_sha256": hashlib.sha256(iwad.read_bytes()).hexdigest(),
            "sound_for_controller": False, "episode_timeout_seconds": args.timeout_seconds}
        (args.out / "environment.json").write_text(json.dumps(environment, indent=2))
        emit({"event": "clock_probe", "before_tic": before, "after_tic": after,
              "wall_seconds": elapsed, "no_advance_calls_during_wait": True,
              "refresh_calls_before_control": 2})
        with (args.out / "backend-setup.txt").open("w") as diagnostics, contextlib.redirect_stdout(diagnostics):
            backend = Backend(session, args.out, emit)
        executor = Executor(backend, emit)
        emit({"event": "ready", "presentation": "full",
              "operations": ["submit", "cancel", "clock", "finish"],
              "command_contract": {
                  "submit": {"op": "submit", "id": "new nonempty string",
                      "expected_sequence": "latest integer observation sequence",
                      "valid_until_ns": "runtime monotonic ns, at most 30s ahead",
                      "steps": [{"op": "hold", "keys": ["1-4 exact binding names"],
                                 "duration_ms": "1-5000"},
                                {"op": "observe"}]},
                  "coast": {"op": "coast", "duration_ms": "1-5000",
                            "sample_ms": "50-1000", "input_authority": False},
                  "limits": {"steps": "1-16", "total_hold_ms": 10000,
                             "implicit_queue": False}},
              "task": "Exit continuously advancing Freedoom MAP01",
              "bindings": {"Left/Right": "turn", "Up or w": "forward",
                           "Down or s": "back", "a/d": "strafe",
                           "e or Return": "use", "space": "attack",
                           "Shift_L": "run"},
              "prohibited": ["pause", "save state", "API action selection",
                             "automap", "object labels", "sector labels"]})
        backend.snapshot("initial", 0)
        control_started_ns = time.perf_counter_ns()
        for line in sys.stdin:
            try:
                command = json.loads(line)
                emit({"event": "command", "command": command,
                      "received_ns": time.perf_counter_ns()})
                if command["op"] == "submit":
                    executor.submit(command["id"], command["steps"],
                                    command["expected_sequence"], command["valid_until_ns"])
                elif command["op"] == "cancel":
                    executor.cancel(command["id"])
                elif command["op"] == "clock":
                    emit({"event": "clock", "runtime_ns": time.perf_counter_ns(),
                          "sequence": backend.sequence})
                elif command["op"] == "finish":
                    executor.close()
                    if not game.is_episode_finished():
                        game.advance_action(1, True)
                    finished = game.is_episode_finished()
                    dead = game.is_player_dead()
                    wall_ns = time.perf_counter_ns() - control_started_ns
                    map_exit = bool(finished and not dead
                                    and wall_ns < (args.timeout_seconds - 5) * 1_000_000_000)
                    deaths = int(game.get_game_variable(vd.GameVariable.DEATHCOUNT))
                    kills = int(game.get_game_variable(vd.GameVariable.KILLCOUNT))
                    score = {"event": "post_control_score", "map": "MAP01", "skill": args.skill,
                        "map_exit": map_exit, "episode_finished": finished,
                        "player_dead": dead, "wall_control_ns": wall_ns,
                        "death_count": deaths, "kill_count": kills,
                        "one_life_map_exit": bool(map_exit and deaths == 0),
                        "episode_timeout_seconds": args.timeout_seconds,
                        "reward": game.get_total_reward(),
                        "scorer_refresh_calls_after_control": 1}
                    (args.out / "score.json").write_text(json.dumps(score, indent=2))
                    emit(score)
                    break
                else:
                    raise ValueError("unsupported command")
            except (ValueError, TypeError, KeyError, Expired) as error:
                emit({"event": "rejected", "reason": str(error)})
    finally:
        if executor is not None:
            executor.close()
        if backend is not None:
            try:
                backend.close()
            finally:
                (args.out / "owner-events.json").write_text(
                    json.dumps(backend.owner.records, indent=2))
        if game is not None:
            game.close()
        if session is not None:
            if (session.tmp / "doom.ini").exists():
                shutil.copy2(session.tmp / "doom.ini", args.out / "doom.ini")
            session.close()
            shutil.rmtree(session.tmp)


if __name__ == "__main__":
    main()
