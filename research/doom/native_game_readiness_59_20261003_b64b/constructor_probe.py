"""Post-failure writable-CWD component test. No display or game init/action."""
from pathlib import Path
import os
import vizdoom as vd

os.environ.pop('DISPLAY', None)
print('cwd', Path.cwd(), flush=True)
print('BEFORE_DoomGame', flush=True)
game = vd.DoomGame()
print('AFTER_DoomGame', flush=True)
game.load_config(str(Path(vd.__file__).parent / 'scenarios/basic.cfg'))
print('AFTER_load_config', flush=True)
config = Path('/tmp/component.ini')
config.write_text('[Doom.Bindings]\nspace=+attack\n')
game.set_doom_config_path(str(config))
game.set_mode(vd.Mode.ASYNC_SPECTATOR)
game.set_seed(7)
game.set_ticrate(35)
game.set_episode_timeout(210)
game.set_window_visible(True)
game.set_sound_enabled(False)
game.set_console_enabled(False)
game.set_render_hud(True)
game.set_render_all_frames(True)
game.set_available_game_variables([vd.GameVariable.KILLCOUNT,
    vd.GameVariable.DEATHCOUNT, vd.GameVariable.SELECTED_WEAPON_AMMO])
print('AFTER_configuration_NO_INIT', flush=True)
game.close()
print('AFTER_close_NO_INIT', flush=True)
