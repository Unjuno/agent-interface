"""One-shot no-input MAP01 startup probe for the pinned WSLc image."""

import hashlib
import json
import pathlib
import time

import vizdoom as vzd


package = pathlib.Path(vzd.__file__).resolve().parent
game = vzd.DoomGame()
game.set_doom_game_path(str(package / "freedoom2.wad"))
game.set_doom_map("MAP01")
game.set_window_visible(True)
game.set_screen_resolution(vzd.ScreenResolution.RES_640X480)
started_ns = time.monotonic_ns()
game.init()
game.new_episode()
state = game.get_state()
if state is None or state.screen_buffer is None:
    raise RuntimeError("MAP01 produced no initial screen buffer")
screen = state.screen_buffer
result = {
    "status": "PASS_TARGET_STARTUP_NO_INPUT",
    "engine": "ViZDoom",
    "map": "MAP01",
    "iwad_sha256": hashlib.sha256((package / "freedoom2.wad").read_bytes()).hexdigest(),
    "screen_shape": list(screen.shape),
    "screen_sha256": hashlib.sha256(screen.tobytes()).hexdigest(),
    "episode_finished": bool(game.is_episode_finished()),
    "ammo1": float(game.get_game_variable(vzd.GameVariable.AMMO1)),
    "ammo2": float(game.get_game_variable(vzd.GameVariable.AMMO2)),
    "startup_elapsed_ns": time.monotonic_ns() - started_ns,
    "input_events_sent": 0,
}
game.close()
result["closed_normally"] = True
print(json.dumps(result, sort_keys=True))
