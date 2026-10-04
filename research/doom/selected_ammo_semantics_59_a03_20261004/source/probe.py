import hashlib, json, pathlib, time
import numpy as np
from PIL import Image
import vizdoom
from vizdoom import DoomGame, GameVariable, ScreenResolution
from doom_hud_signal_v3 import DoomStatusNumberReader

out=pathlib.Path('/out')
wad=pathlib.Path(vizdoom.__file__).parent/'freedoom2.wad'
game=DoomGame()
game.load_config(str(pathlib.Path(vizdoom.__file__).parent/'scenarios'/'doom2.cfg'))
game.set_doom_game_path(str(wad))
game.set_screen_resolution(ScreenResolution.RES_640X480)
game.set_window_visible(False)
variables=[GameVariable.HEALTH,GameVariable.SELECTED_WEAPON,GameVariable.SELECTED_WEAPON_AMMO]+[getattr(GameVariable,f'AMMO{i}') for i in range(10)]
for v in variables: game.add_available_game_variable(v)
readers={name:DoomStatusNumberReader(wad,signal_id=name) for name in ('health','ammo')}
game.init(); game.new_episode()
rows=[]
for sequence,(phase,ticks) in enumerate((('initial',0),('coast',35))):
    if ticks: game.advance_action(ticks,True)
    tic_before_state=int(game.get_episode_time())
    state=game.get_state()
    tic_after_state=int(game.get_episode_time())
    frame=Image.fromarray(np.asarray(state.screen_buffer).transpose(1,2,0))
    png=out/f'{phase}.png'; frame.save(png)
    binding={'focus':'not_applicable_in_memory','surface':'vizdoom_screen_buffer','geometry':[0,0,640,480]}
    observation={'sequence':sequence,'capture_ns':time.perf_counter_ns(),'pointer_binding':binding,'image':png.name}
    signal_results={name:reader.read_frame(observation,frame) for name,reader in readers.items()}
    direct_before=int(game.get_episode_time())
    direct={v.name:float(game.get_game_variable(v)) for v in variables}
    direct_after=int(game.get_episode_time())
    state_values={v.name:float(state.game_variables[i]) for i,v in enumerate(variables)}
    rows.append({'phase':phase,'episode_tic_before_state':tic_before_state,'episode_tic_after_state':tic_after_state,'episode_tic_before_direct_reads':direct_before,'episode_tic_after_direct_reads':direct_after,'state_number':int(state.number),'screen_size':[frame.width,frame.height],'variables_order':[v.name for v in variables],'direct':direct,'state_game_variables':state_values,'signals':signal_results,'frame_png':png.name,'frame_sha256':hashlib.sha256(png.read_bytes()).hexdigest(),'binding_metadata_note':'synthetic in-memory binding metadata; this is not a live X11 pointer/focus identity'} )
raw={'schema':'selected-ammo-hud-reader-a03-v1','run_id':'59-selected-ammo-semantics-a03-20261004','wad_path':str(wad),'wad_sha256':hashlib.sha256(wad.read_bytes()).hexdigest(),'inputs_submitted':[],'rows':rows}
(out/'raw.json').write_text(json.dumps(raw,indent=2))
game.close()
print(json.dumps({'run_id':raw['run_id'],'wad_sha256':raw['wad_sha256'],'rows':rows},indent=2))
