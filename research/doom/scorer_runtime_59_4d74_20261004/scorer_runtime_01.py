from pathlib import Path
import json,time,hashlib,importlib.metadata
import vizdoom as vd
out=Path('/out');wad=Path('/study/fixture-input/freedoom2.wad')
record={'version':importlib.metadata.version('vizdoom'),'wad_sha256':hashlib.sha256(wad.read_bytes()).hexdigest(),'mode':'ASYNC_PLAYER','positive_inputs':0,'samples':[],'status':'STARTED'}
game=vd.DoomGame()
try:
    assert record['version']=='1.3.0'
    assert record['wad_sha256']=='a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b'
    game.set_doom_scenario_path(str(wad));game.set_doom_map('map01')
    game.set_mode(vd.Mode.ASYNC_PLAYER);game.set_window_visible(False)
    game.set_available_buttons([]);game.set_episode_timeout(175);game.set_seed(40104)
    game.init();game.new_episode()
    def sample(label):
        row={'label':label,'started_ns':time.perf_counter_ns(),'tic_before':int(game.get_episode_time()),'killcount':game.get_game_variable(vd.GameVariable.KILLCOUNT),'deathcount':game.get_game_variable(vd.GameVariable.DEATHCOUNT),'tic_after':int(game.get_episode_time()),'finished_ns':time.perf_counter_ns()}
        record['samples'].append(row);return row
    first=sample('before_passive_wait');time.sleep(.15);second=sample('after_passive_wait')
    before=time.perf_counter_ns();tic_before=int(game.get_episode_time())
    game.advance_action(1,True)
    after=time.perf_counter_ns();tic_after=int(game.get_episode_time())
    sample('after_one_tic_update')
    record['refresh']={'started_ns':before,'returned_ns':after,'elapsed_ns':after-before,'tic_before':tic_before,'tic_after':tic_after}
    record['available_buttons']=[str(b)for b in game.get_available_buttons()]
    record['passive_clock_advanced']=second['tic_before']>first['tic_before']
    record['refresh_returned_with_advance']=tic_after>tic_before
    record['status']='PASS_NEUTRAL_REFRESH_RETURN_SCOPED' if record['passive_clock_advanced'] and record['refresh_returned_with_advance'] and not record['available_buttons'] else 'FAIL_QUALIFICATION'
except BaseException as exc:
    record['status']='STOP';record['error']={'type':type(exc).__name__,'message':str(exc)}
finally:
    try:game.close();record['game_close_returned']=True
    except BaseException as exc:record['game_close_returned']=False;record['close_error']=repr(exc)
    record['scope']='Neutral headless engine only; no kill producer epoch, physical release, useful effect/recovery or live controller qualification.'
    (out/'RESULT.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
raise SystemExit(0 if record['status']=='PASS_NEUTRAL_REFRESH_RETURN_SCOPED' and record['game_close_returned'] else 1)
