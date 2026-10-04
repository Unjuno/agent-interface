from pathlib import Path
import ast,json,time,hashlib,sys
import vizdoom as vd
from independent_progress_clock_v2 import ProgressSample
source=Path('/source/session_map01_v15.py').read_bytes();node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='_coherent_progress_sample');scope={'ProgressSample':ProgressSample,'time':time};exec(compile(ast.Module(body=[node],type_ignores=[]),'frozen-helper','exec'),scope)
g=vd.DoomGame();r={'source_sha256':hashlib.sha256(source).hexdigest(),'buttons':[],'positive_input_calls':0,'samples':[],'ack_attempts':0,'status':'STARTED'}
def sample(label):
 before=g.get_episode_time();s=scope['_coherent_progress_sample'](g,vd.GameVariable,1);r['samples'].append({'label':label,'tic':before,'state':s.as_dict(),'observed_host_ns':time.perf_counter_ns()})
try:
 g.set_doom_scenario_path('/wad/freedoom2.wad');g.set_doom_map('map01');g.set_mode(vd.Mode.ASYNC_PLAYER);g.set_window_visible(False);g.set_available_buttons([]);g.set_episode_timeout(35);g.set_seed(40106);g.init();sample('initial');start=time.perf_counter_ns();time.sleep(2);r['passive_elapsed_ns']=time.perf_counter_ns()-start;sample('passive');r['ack_attempts']=1
 try:g.advance_action(1,True);r['ack_returned']=True
 except Exception as e:r['ack_error']={'type':type(e).__name__,'message':str(e)}
 sample('after_ack');p=r['samples'][1]['state'];a=r['samples'][2]['state'];r['status']='PASS_TERMINAL_VISIBLE_ONLY_AFTER_UPDATE_SCOPED' if not p['episode_finished'] and a['episode_finished'] else 'HOLD_TERMINAL_VISIBILITY_CONTRAST_UNEXPOSED'
except BaseException as e:r['status']='STOP';r['error']={'type':type(e).__name__,'message':str(e)}
finally:
 try:g.close();r['close_returned']=True
 except BaseException as e:r['close_error']=repr(e)
 r['running_after_close']=g.is_running();Path('/out/RESULT.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
sys.exit(0 if r['status'].startswith('PASS') else 1)
