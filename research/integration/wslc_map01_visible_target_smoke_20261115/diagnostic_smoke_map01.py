"""Bounded phase diagnostic for a private-Xvfb ViZDoom MAP01 startup."""

import hashlib
import json
import pathlib
import time

import vizdoom as vzd


def phase(name):
    print(json.dumps({"phase": name, "monotonic_ns": time.monotonic_ns()}), flush=True)


phase("python_and_vizdoom_imported")
package = pathlib.Path(vzd.__file__).resolve().parent
game = vzd.DoomGame()
game.set_doom_game_path(str(package / "freedoom2.wad"))
game.set_doom_map("MAP01")
game.set_window_visible(True)
game.set_screen_resolution(vzd.ScreenResolution.RES_640X480)
phase("configuration_complete_before_init")
game.init()
phase("init_complete")
game.new_episode()
phase("new_episode_complete")
state = game.get_state()
phase("initial_state_received")
if state is None or state.screen_buffer is None:
    raise RuntimeError("MAP01 produced no initial screen buffer")
screen = state.screen_buffer
result = {
    "status": "PASS_TARGET_STARTUP_NO_INPUT",
    "map": "MAP01",
    "iwad_sha256": hashlib.sha256((package / "freedoom2.wad").read_bytes()).hexdigest(),
    "screen_shape": list(screen.shape),
    "screen_sha256": hashlib.sha256(screen.tobytes()).hexdigest(),
    "episode_finished": bool(game.is_episode_finished()),
    "ammo1": float(game.get_game_variable(vzd.GameVariable.AMMO1)),
    "ammo2": float(game.get_game_variable(vzd.GameVariable.AMMO2)),
    "input_events_sent": 0,
}
game.close()
phase("game_closed_normally")
print(json.dumps(result, sort_keys=True), flush=True)
