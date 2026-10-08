from pathlib import Path
import hashlib,importlib.metadata,json,os,platform,time
import vizdoom as vd

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'raw.json'
os.environ['HOME']=str(ROOT/'home')
os.environ['XDG_CONFIG_HOME']=str(ROOT/'config')
os.environ['XDG_CACHE_HOME']=str(ROOT/'cache')
os.environ['SDL_VIDEODRIVER']='dummy'
os.chdir(ROOT)
EXPECTED_WAD='a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b'
record={"allocation":"SCORER-REFRESH-59-ASYNC-SPECTATOR-01","status":"STARTED","version":importlib.metadata.version('vizdoom'),"platform":platform.platform(),"machine":platform.machine(),"mode_requested":"ASYNC_SPECTATOR","positive_input_calls":0,"available_buttons":None,"samples":[]}
game=vd.DoomGame()
def sample(label):
    start=time.perf_counter_ns()
    episode_before=int(game.get_episode_time())
    state=game.get_state()
    state_tic=None if state is None else int(state.tic)
    state_vars=None if state is None else [float(v) for v in state.game_variables]
    kill_live=float(game.get_game_variable(vd.GameVariable.KILLCOUNT))
    death_live=float(game.get_game_variable(vd.GameVariable.DEATHCOUNT))
    episode_after=int(game.get_episode_time())
    row={"label":label,"read_start_ns":start,"episode_before":episode_before,"state_tic":state_tic,"state_variables":state_vars,"kill_live":kill_live,"death_live":death_live,"episode_after":episode_after,"read_end_ns":time.perf_counter_ns()}
    record['samples'].append(row)
    return row
try:
    if record['version']!='1.3.0': raise RuntimeError('unexpected ViZDoom version')
    wad=Path(vd.__file__).parent/'freedoom2.wad'
    wad_hash=hashlib.sha256(wad.read_bytes()).hexdigest()
    record.update({"wad_path":str(wad),"wad_sha256":wad_hash,"mode_actual":None,"ticrate":None})
    if wad_hash!=EXPECTED_WAD: raise RuntimeError('WAD hash mismatch')
    game.set_doom_game_path(str(wad)); game.set_doom_scenario_path(''); game.set_doom_map('MAP01')
    game.set_mode(vd.Mode.ASYNC_SPECTATOR); game.set_ticrate(35); game.set_seed(40104)
    game.set_episode_timeout(175); game.set_window_visible(False); game.set_sound_enabled(False)
    game.set_available_buttons([])
    game.set_available_game_variables([vd.GameVariable.DEATHCOUNT,vd.GameVariable.KILLCOUNT])
    game.init(); game.new_episode()
    record['mode_actual']=str(game.get_mode()); record['ticrate']=int(game.get_ticrate())
    if game.get_mode()!=vd.Mode.ASYNC_SPECTATOR or game.get_ticrate()!=35: raise RuntimeError('actual mode or ticrate mismatch')
    record['available_buttons']=[str(x) for x in game.get_available_buttons()]
    record['initial']=sample('initial')
    time.sleep(0.150); record['after_passive_150ms']=sample('after_passive_150ms')
    record['before_acknowledged_update']=sample('before_acknowledged_update')
    update_start=time.perf_counter_ns(); update_tic_before=int(game.get_episode_time())
    game.advance_action(1,True)
    update_return=time.perf_counter_ns(); update_tic_after=int(game.get_episode_time())
    record['update']={"started_ns":update_start,"returned_ns":update_return,"elapsed_ns":update_return-update_start,"episode_before":update_tic_before,"episode_after":update_tic_after,"delta":update_tic_after-update_tic_before}
    record['after_acknowledged_update']=sample('after_acknowledged_update')
    time.sleep(0.150); record['after_second_passive_150ms']=sample('after_second_passive_150ms')
    state_delta=(record['after_acknowledged_update']['state_tic'] is not None and record['before_acknowledged_update']['state_tic'] is not None and record['after_acknowledged_update']['state_tic']>record['before_acknowledged_update']['state_tic'])
    if record['available_buttons'] or not state_delta:
        record['status']='FAIL_QUALIFICATION'
    elif record['update']['delta']>1:
        record['status']='PASS_COUNTEREXAMPLE_EXACT_ONE_TIC_GUARD'
    else:
        record['status']='PASS_NO_COUNTEREXAMPLE_IN_SINGLE_RUN'
except BaseException as error:
    record['status']='STOP';record['error']={"type":type(error).__name__,"message":str(error)}
finally:
    try:
        game.close();record['game_close_returned']=True
    except BaseException as error:
        record['game_close_returned']=False;record['close_error']={"type":type(error).__name__,"message":str(error)}
    record['scope']='One neutral, headless macOS runtime process only; no X server, model, positive input, task-effect measurement, physical release, or post-invalidation recovery.'
    OUT.write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
print(json.dumps(record,sort_keys=True))
raise SystemExit(0 if record['status'].startswith('PASS_') and record.get('game_close_returned') else 1)
