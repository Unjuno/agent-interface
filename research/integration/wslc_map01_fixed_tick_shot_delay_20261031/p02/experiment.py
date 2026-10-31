import hashlib, json
from pathlib import Path
import vizdoom as vd

pkg=Path(vd.__file__).resolve().parent
wad=pkg/'freedoom2.wad'
buttons=[vd.Button.MOVE_FORWARD,vd.Button.TURN_LEFT,vd.Button.ATTACK]
variables=[vd.GameVariable.POSITION_X,vd.GameVariable.POSITION_Y,vd.GameVariable.ANGLE,vd.GameVariable.HEALTH,vd.GameVariable.KILLCOUNT,vd.GameVariable.SELECTED_WEAPON_AMMO]
results=[]
for arm in ['withhold','fire','fire','withhold']:
 game=vd.DoomGame()
 try:
  game.set_doom_game_path(str(wad)); game.set_doom_scenario_path(''); game.set_doom_map('MAP01'); game.set_mode(vd.Mode.PLAYER); game.set_seed(991031); game.set_doom_skill(1); game.set_episode_timeout(2100); game.set_window_visible(False); game.set_sound_enabled(False); game.set_screen_resolution(vd.ScreenResolution.RES_640X480); game.set_available_buttons(buttons); game.set_available_game_variables(variables); game.set_labels_buffer_enabled(True); game.init(); game.new_episode()
  def snapshot(label):
   s=game.get_state()
   return {'label':label,'tic':game.get_episode_time(),'variables':[game.get_game_variable(v) for v in variables],'screen_sha256':hashlib.sha256(s.screen_buffer.tobytes()).hexdigest() if s else None,'labels':sorted(x.object_name for x in s.labels) if s else []}
  def run(action,ticks):
   for _ in range(ticks): game.make_action(action,1)
  prefix=[]
  for label,action,ticks in [('forward',[1,0,0],70),('settle',[0,0,0],28),('turn',[0,1,0],32),('partial_attack',[0,0,1],3),('released',[0,0,0],70)]:
   run(action,ticks); prefix.append(snapshot(label))
  run([0,0,1] if arm=='fire' else [0,0,0],12); after=snapshot('after_action')
  run([0,0,0],70); final=snapshot('final')
  results.append({'arm':arm,'prefix':prefix,'after':after,'final':final})
 finally: game.close()
print(json.dumps({'iwad_sha256':hashlib.sha256(wad.read_bytes()).hexdigest(),'seed':991031,'mode':'PLAYER fixed tics','variables':[str(v) for v in variables],'runs':results},indent=2))
