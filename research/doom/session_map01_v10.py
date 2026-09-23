"""MAP01 v10 emits typed HUD evidence before full artifact publication."""

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
sys.path.insert(0, str(HERE.parent / "observation_gating"))
sys.path.insert(0, str(HERE.parent / "live_control"))
from executor_v10 import Executor
from lease import Expired
from doom_typed_coast_backend_v1 import Backend, suite
from doom_hud_signal_v3 import DoomStatusNumberReader


FIXTURE_SCHEMA = "map01_os_input_fixture_v1"
SETUP_INPUT_CONTRACT = ("fixture state reached through the same X11 Executor and "
                        "recorded OS-input/coast programs; save is setup-only")


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def wait_for_stable_file(path, timeout=5):
    path = Path(path)
    deadline = time.monotonic() + timeout
    previous = None
    while time.monotonic() < deadline:
        if path.is_file() and path.stat().st_size > 0:
            current = (path.stat().st_size, path.stat().st_mtime_ns)
            if current == previous:
                return current[0]
            previous = current
        time.sleep(.05)
    raise TimeoutError(f"save file did not stabilize: {path}")


def validate_fixture_manifest(manifest_path, vizdoom_version, iwad_sha256, skill):
    manifest_path = Path(manifest_path).resolve()
    fixture = json.loads(manifest_path.read_text(encoding="utf-8"))
    if fixture.get("schema") != FIXTURE_SCHEMA:
        raise ValueError("unsupported fixture manifest")
    if fixture.get("map") != "MAP01" or fixture.get("skill") != skill:
        raise ValueError("fixture map/skill mismatch")
    if fixture.get("vizdoom") != vizdoom_version or fixture.get("iwad_sha256") != iwad_sha256:
        raise ValueError("fixture engine/IWAD mismatch")
    save_name = fixture.get("save_file")
    if (not isinstance(save_name, str) or Path(save_name).name != save_name or
            Path(save_name).suffix.lower() != ".png"):
        raise ValueError("fixture save_file must be a sibling PNG basename")
    save_path = (manifest_path.parent / save_name).resolve()
    if file_sha256(save_path) != fixture.get("save_sha256"):
        raise ValueError("fixture save hash mismatch")
    frame_name = fixture.get("source_frame")
    if not isinstance(frame_name, str) or Path(frame_name).name != frame_name:
        raise ValueError("fixture source_frame must be a sibling basename")
    frame_path = (manifest_path.parent / frame_name).resolve()
    if file_sha256(frame_path) != fixture.get("source_frame_sha256"):
        raise ValueError("fixture source-frame hash mismatch")
    if fixture.get("setup_input_contract") != SETUP_INPUT_CONTRACT:
        raise ValueError("fixture setup-input contract mismatch")
    source = fixture.get("source_observation")
    if not isinstance(fixture.get("episode_tic"), int) or fixture["episode_tic"] < 0:
        raise ValueError("fixture episode tic missing")
    if not isinstance(source, dict) or source.get("event") != "observation" or source.get("exact") is not True:
        raise ValueError("fixture exact source observation missing")
    return fixture, save_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--skill", type=int, choices=range(1,6), default=1)
    parser.add_argument("--fixture-out", type=Path)
    parser.add_argument("--load-fixture-manifest", type=Path)
    args = parser.parse_args()
    if args.fixture_out is not None and args.fixture_out.suffix.lower() != ".png":
        parser.error("fixture-out must be a .png save container")
    args.out.mkdir(parents=True, exist_ok=False)
    lock = threading.RLock()
    session = game = executor = backend = None
    control_started_ns = None
    latest_observation = None

    def emit(row):
        nonlocal latest_observation
        with lock:
            if row.get("event") == "observation":
                latest_observation = dict(row)
            row["emit_ns"] = time.perf_counter_ns()
            encoded = json.dumps(row)
            with (args.out / "events.jsonl").open("a") as stream:
                stream.write(encoded + "\n")
            with (args.out / "delivered.jsonl").open("a") as stream:
                stream.write(encoded + "\n")
            print(encoded, flush=True)

    sources = {}
    for path in (Path(__file__), HERE.parent / "live_control/session_v8.py",
                 HERE.parent / "live_control/executor_v10.py",
                 HERE.parent / "live_control/lease.py",
                 HERE.parent / "live_control/session_v9.py",
                 HERE.parent / "live_control/session_v10.py",
                 HERE.parent / "live_control/coast_backend_v1.py",
                 HERE / "doom_typed_coast_backend_v1.py",
                 HERE / "doom_typed_observation_v1.py",
                 HERE / "doom_hud_signal_v3.py",
                 HERE / "doom_hud_signal_v2.py",
                 HERE / "doom_hud_signal_v1.py"):
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
        iwad_sha256 = file_sha256(iwad)
        loaded_fixture = None
        if args.load_fixture_manifest is not None:
            manifest_path = args.load_fixture_manifest.resolve()
            fixture, save_path = validate_fixture_manifest(
                manifest_path, vd.__version__, iwad_sha256, args.skill)
            before_load_tic = game.get_episode_time()
            engine_load_path = session.tmp / "fixture-load.png"
            shutil.copy2(save_path, engine_load_path)
            game.load(str(engine_load_path))
            loaded_fixture = {
                "manifest": str(manifest_path), "manifest_sha256": file_sha256(manifest_path),
                "save": str(save_path), "save_sha256": fixture["save_sha256"],
                "before_load_tic": before_load_tic, "after_load_tic": game.get_episode_time(),
                "source_episode_tic": fixture["episode_tic"],
                "setup_input_contract": fixture["setup_input_contract"],
            }
        environment = {"vizdoom": vd.__version__, "mode": str(game.get_mode()),
            "ticrate": game.get_ticrate(), "seed": args.seed, "map": "MAP01", "skill": args.skill,
            "scenario_path": None, "iwad": str(iwad),
            "iwad_sha256": iwad_sha256,
            "loaded_fixture": loaded_fixture,
            "sound_for_controller": False, "episode_timeout_seconds": args.timeout_seconds}
        (args.out / "environment.json").write_text(json.dumps(environment, indent=2))
        emit({"event": "clock_probe", "before_tic": before, "after_tic": after,
              "wall_seconds": elapsed, "no_advance_calls_during_wait": True,
              "refresh_calls_before_control": 2})
        with (args.out / "backend-setup.txt").open("w") as diagnostics, contextlib.redirect_stdout(diagnostics):
            signal_readers = {
                name: DoomStatusNumberReader(iwad, signal_id=name)
                for name in ("health", "ammo")}
            backend = Backend(session, args.out, emit, signal_readers)
        executor = Executor(backend, emit)
        operations = ["submit", "cancel", "clock", "finish"]
        if args.fixture_out is not None:
            operations.append("save_fixture")
        prohibited = ["pause", "API action selection", "automap", "object labels", "sector labels"]
        if args.fixture_out is None:
            prohibited.append("save state")
        emit({"event": "ready", "presentation": "full",
              "operations": operations,
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
                             "implicit_queue": False},
                  "accepted_attestation": "SHA-256 of canonical validated step JSON"},
              "observation_contract": {
                  "early": "doom-typed-observation-v1 before transport/artifact publication",
                  "later": "exact full observation with matching epoch and RGB SHA-256",
                  "typed_signals": ["health", "ammo"],
                  "early_grants_input_authority": False},
              "task": "Exit continuously advancing Freedoom MAP01",
              "bindings": {"Left/Right": "turn", "Up or w": "forward",
                           "Down or s": "back", "a/d": "strafe",
                           "e or Return": "use", "space": "attack",
                           "Shift_L": "run"},
              "fixture": loaded_fixture,
              "prohibited": prohibited})
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
                elif command["op"] == "save_fixture":
                    if args.fixture_out is None:
                        raise ValueError("save_fixture is unavailable in measured control")
                    executor.close()
                    backend.snapshot("fixture-source", 0)
                    save_path = args.fixture_out.resolve()
                    save_path.parent.mkdir(parents=True, exist_ok=True)
                    engine_save_path = session.tmp / "fixture-save.png"
                    game.save(str(engine_save_path))
                    game.advance_action(1, True)
                    wait_for_stable_file(engine_save_path)
                    shutil.copy2(engine_save_path, save_path)
                    source_frame = save_path.with_name(save_path.stem + ".source.png")
                    shutil.copy2(Path(latest_observation["image"]), source_frame)
                    fixture = {
                        "schema": FIXTURE_SCHEMA,
                        "map": "MAP01", "skill": args.skill, "seed": args.seed,
                        "vizdoom": vd.__version__, "iwad_sha256": iwad_sha256,
                        "save_file": save_path.name,
                        "save_sha256": file_sha256(save_path),
                        "source_frame": source_frame.name,
                        "source_frame_sha256": file_sha256(source_frame),
                        "episode_tic": game.get_episode_time(),
                        "source_observation": latest_observation,
                        "setup_input_contract": SETUP_INPUT_CONTRACT,
                        "runtime_events": str((args.out / "events.jsonl").resolve()),
                    }
                    if loaded_fixture is not None:
                        fixture["parent_fixture"] = {
                            "manifest_sha256": loaded_fixture["manifest_sha256"],
                            "save_sha256": loaded_fixture["save_sha256"],
                            "source_episode_tic": loaded_fixture["source_episode_tic"],
                            "loaded_episode_tic": loaded_fixture["after_load_tic"],
                        }
                    manifest_path = save_path.with_suffix(".json")
                    manifest_path.write_text(json.dumps(fixture, indent=2) + "\n",
                                             encoding="utf-8", newline="\n")
                    emit({"event": "fixture_saved", "manifest": str(manifest_path),
                          "save": str(save_path), "save_sha256": fixture["save_sha256"],
                          "episode_tic": fixture["episode_tic"],
                          "source_sequence": latest_observation["sequence"]})
                    break
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
