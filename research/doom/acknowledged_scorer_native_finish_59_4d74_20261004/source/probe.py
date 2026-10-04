from pathlib import Path
import json,time
import vizdoom as vd
from acknowledged_scorer_v1 import AcknowledgedSampler
from session_map01_v16 import ObservedGameProxy
from session_map01_v15 import _coherent_progress_sample
from map01_scorer_stdio_adapter_v1 import ScorerFileSink
out=Path('/out');rows=[];sink=ScorerFileSink(out);sampler=AcknowledgedSampler(_coherent_progress_sample,'native-finish-40109',rows.append)
g=vd.DoomGame();r={'status':'STARTED','positive_input_calls':0}
proxy=ObservedGameProxy(g,lambda:sink.direct(sampler(proxy,vd.GameVariable,10),time.perf_counter_ns),sampler)
try:
 g.set_doom_scenario_path('/wad/freedoom2.wad');g.set_doom_map('map01');g.set_mode(vd.Mode.ASYNC_SPECTATOR);g.set_ticrate(35);g.set_window_visible(False);g.set_available_buttons([]);g.set_available_game_variables([vd.GameVariable.DEATHCOUNT,vd.GameVariable.KILLCOUNT]);g.set_episode_timeout(350);g.set_seed(40109);proxy.init()
 first=sampler(proxy,vd.GameVariable,10);sink.direct(first,time.perf_counter_ns);r['initial']=first.as_dict()
 start=time.perf_counter_ns();time.sleep(12);r['passive_elapsed_ns']=time.perf_counter_ns()-start
 proxy.advance_action(1,True);r['external_ack']=dict(sampler.external_ack);before_close=sampler.update_sequence
 proxy.close();r['close_returned']=True;r['updates_before_close']=before_close;r['updates_after_close']=sampler.update_sequence;r['running_after_close']=g.is_running();r['final']=sampler.last.as_dict()
 assert sampler.update_sequence==before_close and not g.is_running();assert sampler.last.episode_finished and not sampler.last.map_exit;assert sampler.last.producer['observation_status']=='EXTERNAL_UPDATE_RETURNED';assert [e['kind'] for e in sink.events]==['EPISODE_FINISHED_NO_EXIT']
 r['status']='PASS_NATIVE_EXTERNAL_FINISH_COMPOSITION_SCOPED'
except BaseException as e:
 r['status']='STOP';r['error']={'type':type(e).__name__,'message':str(e)}
finally:
 try:
  if not proxy.closed:proxy.close()
 except BaseException as e:r['cleanup_error']={'type':type(e).__name__,'message':str(e)}
 r['running_after_cleanup']=g.is_running();r['update_rows']=rows;r['scorer_summary']=sink.finalize({'native_construction':True});(out/'RESULT.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
raise SystemExit(0 if r['status'].startswith('PASS') else 1)
