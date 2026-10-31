import hashlib,json
from pathlib import Path
import vizdoom as vd
wad=Path(vd.__file__).resolve().parent/'freedoom2.wad'
runs=[]
for arm in ['idle','attack','attack','idle']:
 g=vd.DoomGame()
 try:
  g.set_doom_game_path(str(wad));g.set_doom_scenario_path('');g.set_doom_map('MAP01');g.set_mode(vd.Mode.PLAYER);g.set_seed(991031);g.set_doom_skill(1);g.set_episode_timeout(2100);g.set_window_visible(False);g.set_sound_enabled(False);g.set_available_buttons([vd.Button.MOVE_FORWARD,vd.Button.TURN_LEFT,vd.Button.ATTACK]);g.set_available_game_variables([vd.GameVariable.SELECTED_WEAPON_AMMO,vd.GameVariable.HEALTH,vd.GameVariable.KILLCOUNT]);g.init();g.new_episode()
  for action,n in [([1,0,0],70),([0,0,0],28),([0,1,0],32)]:
   for _ in range(n):g.make_action(action,1)
  def snap(phase):
   state=g.get_state();return {'phase':phase,'tic':g.get_episode_time(),'ammo':g.get_game_variable(vd.GameVariable.SELECTED_WEAPON_AMMO),'health':g.get_game_variable(vd.GameVariable.HEALTH),'kills':g.get_game_variable(vd.GameVariable.KILLCOUNT),'screen_sha256':hashlib.sha256(state.screen_buffer.tobytes()).hexdigest()}
  samples=[snap('before')]
  for _ in range(3):g.make_action([0,0,1] if arm=='attack' else [0,0,0],1);samples.append(snap('active'))
  for _ in range(20):g.make_action([0,0,0],1);samples.append(snap('released'))
  runs.append({'arm':arm,'samples':samples})
 finally:g.close()
print(json.dumps({'iwad_sha256':hashlib.sha256(wad.read_bytes()).hexdigest(),'seed':991031,'runs':runs},indent=2))
