from pathlib import Path
import ast,json,sys,time,os,hashlib,importlib.metadata
import vizdoom as vd
out=Path('/out');source=Path('/source/session_map01_v15.py').read_bytes()
tree=ast.parse(source);node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='_GameProxy')
scope={'sys':sys};exec(compile(ast.Module(body=[node],type_ignores=[]),'frozen_proxy','exec'),scope)
def engine_pids():
    found=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            if Path(os.readlink(p/'exe')).name=='vizdoom':found.append(int(p.name))
        except (OSError,PermissionError):pass
    return sorted(found)
record={'source_sha256':hashlib.sha256(source).hexdigest(),'version':importlib.metadata.version('vizdoom'),'positive_inputs':0,'pids_before':engine_pids(),'status':'STARTED'}
game=vd.DoomGame();proxy=None
try:
    assert record['version']=='1.3.0'
    wad=Path('/source/freedoom2.wad')
    record['wad_sha256']=hashlib.sha256(wad.read_bytes()).hexdigest()
    assert record['wad_sha256']=='a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b'
    game.set_doom_scenario_path(str(wad));game.set_doom_map('map01');game.set_mode(vd.Mode.ASYNC_PLAYER)
    game.set_window_visible(False);game.set_available_buttons([]);game.set_episode_timeout(175);game.set_seed(40105)
    def final_sample():
        record['sample_called']=record.get('sample_called',0)+1
        record['sample_proxy_open']=not proxy.closed
        raise RuntimeError('injected final scorer failure')
    proxy=scope['_GameProxy'](game,final_sample);proxy.init()
    record['running_before']=game.is_running();record['pids_running']=engine_pids()
    record['new_engine_pids']=sorted(set(record['pids_running'])-set(record['pids_before']))
    start=time.perf_counter_ns()
    try:proxy.close();record['error_preserved']=False
    except RuntimeError as exc:record['error_preserved']=str(exc)=='injected final scorer failure';record['close_error']=repr(exc)
    record['close_returned_ns']=time.perf_counter_ns();record['close_started_ns']=start
    record['running_after']=game.is_running();record['pids_after']=engine_pids();record['proxy_closed']=proxy.closed
    record['second_close_none']=proxy.close() is None
    record['available_buttons']=[str(x)for x in game.get_available_buttons()]
    checks=[record['running_before'],record['error_preserved'],not record['running_after'],record['proxy_closed'],record['sample_called']==1,record['sample_proxy_open'],record['second_close_none'],not record['available_buttons'],bool(record['new_engine_pids']),not(set(record['new_engine_pids'])&set(record['pids_after']))]
    record['checks']=checks;record['status']='PASS_REAL_ENGINE_FINAL_SAMPLE_FAILURE_CLEANUP_SCOPED' if all(checks)else 'FAIL_QUALIFICATION'
except BaseException as exc:record['status']='STOP';record['error']={'type':type(exc).__name__,'message':str(exc)}
finally:
    if game.is_running():
        record['emergency_cleanup_required']=True
        try:game.close();record['emergency_close_returned']=True
        except BaseException as exc:record['emergency_close_error']=repr(exc)
    record['scope']='One neutral engine with injected final scorer failure; no close-failure recovery, concurrency, controller/gameplay/model/native input or scorer freshness qualification.'
    (out/'RESULT.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
raise SystemExit(0 if record['status']=='PASS_REAL_ENGINE_FINAL_SAMPLE_FAILURE_CLEANUP_SCOPED' else 1)
