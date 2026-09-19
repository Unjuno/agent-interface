"""Model-free save/load capability probe across ViZDoom control modes."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import time

import vizdoom as vd


MODES = (vd.Mode.PLAYER, vd.Mode.ASYNC_PLAYER, vd.Mode.SPECTATOR, vd.Mode.ASYNC_SPECTATOR)


def configure(mode, seed):
    game = vd.DoomGame()
    iwad = Path(vd.__file__).parent / "freedoom2.wad"
    game.set_doom_game_path(str(iwad))
    game.set_doom_scenario_path("")
    game.set_doom_map("MAP01")
    game.set_mode(mode)
    game.set_ticrate(35)
    game.set_seed(seed)
    game.set_doom_skill(1)
    game.set_episode_timeout(35 * 60)
    game.set_window_visible(False)
    game.set_console_enabled(False)
    game.set_sound_enabled(False)
    game.set_screen_resolution(vd.ScreenResolution.RES_640X480)
    game.set_render_hud(True)
    game.set_available_buttons([
        vd.Button.TURN_LEFT, vd.Button.TURN_RIGHT, vd.Button.MOVE_FORWARD,
        vd.Button.MOVE_BACKWARD, vd.Button.MOVE_LEFT, vd.Button.MOVE_RIGHT,
        vd.Button.ATTACK, vd.Button.USE, vd.Button.SPEED])
    return game, iwad


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=990619)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    rows = []
    with tempfile.TemporaryDirectory(prefix="agent-interface-save-load-") as directory:
      engine_root = Path(directory)
      for mode in MODES:
        name = str(mode).split(".")[-1].lower()
        save = engine_root / f"{name}.png"
        retained_save = (args.out / f"{name}.png").resolve()
        game, iwad = configure(mode, args.seed)
        error = None
        try:
            game.init()
            game.new_episode()
            game.advance_action(2, True)
            before_tic = game.get_episode_time()
            game.save(str(save))
            game.advance_action(2, True)
            time.sleep(.1)
            after_save_tic = game.get_episode_time()
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            before_tic = after_save_tic = None
        finally:
            game.close()
        exists = save.is_file()
        load_error = None
        loaded_state = False
        loaded_tic = None
        if exists:
            shutil.copy2(save, retained_save)
            loader, _ = configure(mode, args.seed)
            try:
                loader.init()
                loader.new_episode()
                loader.load(str(save))
                state = loader.get_state()
                loaded_state = state is not None
                loaded_tic = loader.get_episode_time()
            except Exception as exc:
                load_error = f"{type(exc).__name__}: {exc}"
            finally:
                loader.close()
        rows.append({
            "mode": str(mode), "save_call_error": error,
            "save_exists": exists, "save_bytes": save.stat().st_size if exists else 0,
            "save_sha256": hashlib.sha256(save.read_bytes()).hexdigest() if exists else None,
            "before_save_tic": before_tic, "after_save_tic": after_save_tic,
            "load_error": load_error, "loaded_state_available": loaded_state,
            "loaded_episode_tic": loaded_tic,
            "engine_path_has_spaces": " " in str(save),
        })
    report = {
        "schema": "map01_save_load_modes_probe_v2", "vizdoom": vd.__version__,
        "iwad_sha256": hashlib.sha256(iwad.read_bytes()).hexdigest(),
        "seed": args.seed, "model_calls": 0, "rows": rows,
        "scope": "headless API capability probe only; no live X11-input or gameplay claim",
    }
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
