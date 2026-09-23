import json, sys, time, hashlib
from pathlib import Path
import vizdoom as vd
from session_map01_v13 import _coherent_progress_sample

out=Path(sys.argv[1]); out.parent.mkdir(parents=True,exist_ok=True)
rows=[]
strata=(('idle',0),('cpu_load',0),('delayed_read',0))
def burn():
    x=0
    for i in range(250000): x=(x*1664525+i)&0xffffffff
    return x

for stratum,offset_ns in strata:
    g=vd.DoomGame()
    g.load_config(str(Path(vd.scenarios_path)/'basic.cfg'))
    g.set_window_visible(False); g.set_sound_enabled(False); g.set_render_hud(False)
    g.set_mode(vd.Mode.ASYNC_PLAYER); g.set_ticrate(35); g.init(); g.new_episode()
    # C++ DoomGame methods are read-only; proxy records calls without changing them.
    original=g.get_episode_time; getter_log=[]
    class GameProxy:
        def __getattr__(self,name):
            if name=='get_episode_time':
                def observed_getter():
                    s=time.perf_counter_ns(); value=int(original()); e=time.perf_counter_ns()
                    getter_log.append(dict(start_ns=s,end_ns=e,tic=value))
                    return value
                return observed_getter
            return getattr(g,name)
    proxy=GameProxy()
    if offset_ns: time.sleep(offset_ns/1e9)
    for sample in range(12):
        attempts=[]
        for attempt in range(3):
            if stratum=='cpu_load': burn()
            if stratum=='delayed_read': time.sleep(.020)
            first=len(getter_log); start=time.perf_counter_ns(); error=None; result=None
            try: result=_coherent_progress_sample(proxy,vd.GameVariable,600)
            except Exception as exc: error=type(exc).__name__+': '+str(exc)
            finish=time.perf_counter_ns(); reads=getter_log[first:]
            attempts.append(dict(attempt=attempt,start_ns=start,end_ns=finish,
                inter_attempt_delay_from_previous_start_ns=None if attempt==0 else start-attempts[-1]['start_ns'],
                reads=reads,read_count=len(reads),coherent=error is None,error=error,
                sample=None if result is None else result.as_dict()))
        rows.append(dict(stratum=stratum,sample=sample,attempts=attempts,final_tic=int(original()),clock_hz=35))
    g.close()
out.write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows))
print(json.dumps(dict(rows=len(rows),strata=[x[0] for x in strata],vizdoom=vd.__version__,mode=str(vd.Mode.ASYNC_PLAYER))))
