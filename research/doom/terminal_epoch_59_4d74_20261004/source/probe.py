from pathlib import Path
import ast,json,time,sys
from dataclasses import replace
import vizdoom as vd
from independent_progress_clock_v2 import ProgressSample,ProgressClock
node=next(n for n in ast.parse(Path('/source/session_map01_v15.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='_coherent_progress_sample');scope={'ProgressSample':ProgressSample,'time':time};exec(compile(ast.Module(body=[node],type_ignores=[]),'helper','exec'),scope)
g=vd.DoomGame();clock=ProgressClock();r={'status':'STARTED','rows':[],'events':[],'positive_input_calls':0};start=time.perf_counter_ns()
try:
 g.set_doom_scenario_path('/wad/freedoom2.wad');g.set_doom_map('map01');g.set_mode(vd.Mode.ASYNC_PLAYER);g.set_window_visible(False);g.set_available_buttons([]);g.set_episode_timeout(70);g.set_seed(40107);g.init()
 first=scope['_coherent_progress_sample'](g,vd.GameVariable,2);clock.ingest(first);r['initial']=first.as_dict();start=time.perf_counter_ns()
 for i in range(100):
  if time.perf_counter_ns()-start>5_000_000_000:break
  req=time.perf_counter_ns();g.advance_action(1,True);ret=time.perf_counter_ns();tic_before=g.get_episode_time();s=scope['_coherent_progress_sample'](g,vd.GameVariable,2);tic_after=g.get_episode_time();events=clock.ingest(s);r['events']+=events
  state=g.get_state();r['rows'].append({'index':i,'ack_requested_ns':req,'ack_returned_ns':ret,'producer_tic_before':tic_before,'producer_tic_after':tic_after,'frame_tic':None if state is None else state.tic,'sample':s.as_dict(),'events':events})
  if s.episode_finished:
   r['repeat_terminal_events']=clock.ingest(replace(s,sample_ns=time.perf_counter_ns()));break
  time.sleep(max(0,1/35-(time.perf_counter_ns()-req)/1e9))
 tics=[x['producer_tic_before'] for x in r['rows']];r['status']='PASS_ACKNOWLEDGED_TERMINAL_PIPELINE_SCOPED' if len(tics)>1 and all(a<b for a,b in zip(tics,tics[1:])) and all(x['producer_tic_before']==x['producer_tic_after'] for x in r['rows']) and len(r['events'])==1 and r['events'][0]['kind']=='EPISODE_FINISHED_NO_EXIT' and r.get('repeat_terminal_events')==[] else 'HOLD_PIPELINE_CONTRACT'
except BaseException as e:r['status']='STOP';r['error']={'type':type(e).__name__,'message':str(e)}
finally:
 g.close();r['close_returned']=True;r['running_after_close']=g.is_running();Path('/out/RESULT.json').write_text(json.dumps(r,indent=2));print(json.dumps({'status':r['status'],'rows':len(r['rows']),'events':r['events'],'running_after_close':r['running_after_close']}))
sys.exit(0 if r['status'].startswith('PASS') else 1)
