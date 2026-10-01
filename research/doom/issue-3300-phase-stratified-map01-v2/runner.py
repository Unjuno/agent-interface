import hashlib,json,sys,time
from pathlib import Path
import vizdoom as vd
from session_map01_v13 import _coherent_progress_sample

FIX=Path('/fixture/fixture'); manifest=json.loads((FIX/'fixture.json').read_text())
save=FIX/manifest['save_file']
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
assert vd.__version__==manifest['vizdoom']
assert sha(save)==manifest['save_sha256']
assert sha(Path(vd.__file__).parent/'freedoom2.wad')==manifest['iwad_sha256']
print('STAGE pre-init verified',flush=True)
g=vd.DoomGame();g.set_doom_game_path(str(Path(vd.__file__).parent/'freedoom2.wad'))
g.set_doom_scenario_path('');g.set_doom_map(manifest['map']);g.set_doom_skill(manifest['skill'])
g.set_seed(manifest['seed']);g.set_mode(vd.Mode.ASYNC_SPECTATOR);g.set_ticrate(35)
g.set_window_visible(True);g.set_sound_enabled(False);g.set_render_hud(False)
g.set_available_game_variables([vd.GameVariable.KILLCOUNT,vd.GameVariable.DEATHCOUNT])
g.init();print('STAGE initialized',flush=True);g.load(str(save));print('STAGE loaded',flush=True)
g.advance_action(1,True)
before=int(g.get_episode_time())
print(json.dumps(dict(vizdoom=vd.__version__,ticrate=g.get_ticrate(),mode=str(g.get_mode()),
 map=manifest['map'],loaded_tic=before,expected_source_tic=manifest['episode_tic'],
 alive=not g.is_player_dead(),fixture_sha256=sha(FIX/'fixture.json'),save_sha256=sha(save))))
try:
    row=_coherent_progress_sample(g,vd.GameVariable,600)
    after_scorer=int(g.get_episode_time());time.sleep(1.0);after_wait=int(g.get_episode_time())
    print(json.dumps(dict(scorer='PASS',sample=row.as_dict(),tic_after_scorer=after_scorer,
        tic_after_one_second=after_wait,async_advanced=after_wait>after_scorer)))
finally:g.close()

g=vd.DoomGame();g.set_doom_game_path(str(Path(vd.__file__).parent/'freedoom2.wad'))
g.set_doom_scenario_path('');g.set_doom_map(manifest['map']);g.set_doom_skill(manifest['skill'])
g.set_seed(manifest['seed']);g.set_mode(vd.Mode.ASYNC_PLAYER);g.set_ticrate(35)
g.set_window_visible(True);g.set_sound_enabled(False);g.set_render_hud(False)
g.init();g.new_episode();start=int(g.get_episode_time());time.sleep(1.0);end=int(g.get_episode_time())
print(json.dumps(dict(control='fresh_new_episode',mode=str(g.get_mode()),tic_before=start,tic_after=end,advanced=end>start)))
g.close()
