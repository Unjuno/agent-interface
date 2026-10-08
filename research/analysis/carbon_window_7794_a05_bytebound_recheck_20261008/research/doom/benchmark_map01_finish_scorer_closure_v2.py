import json, os, statistics, tempfile, time
from test_map01_telemetry_session_v2 import Game,Scorer,Executor,Backend
from map01_telemetry_session_v2 import CommandStopState,make_v12_command_handler_v2,run_telemetry_control_loop_v2

def pct(xs,p):
    ys=sorted(xs); return ys[min(len(ys)-1,round((len(ys)-1)*p))]
def one():
    rd,wr=os.pipe(); os.write(wr,b'{"op":"finish"}\n'); os.close(wr)
    with tempfile.TemporaryDirectory() as d:
        g=Game(); s=Scorer(g,d); state=CommandStopState(); emitted=[]; score={}
        def finish():
            g.kills=1; g.finished=True
            score.update(map_exit=True,episode_finished=True,player_dead=False,death_count=0,kill_count=1)
        h=make_v12_command_handler_v2(emit=emitted.append,executor=Executor(),backend=Backend(),on_finish=finish,stop_state=state)
        t0=time.perf_counter_ns(); stats,summary,final=run_telemetry_control_loop_v2(fd=rd,scorer=s,command_handler=h,stop_state=state,terminal_score_fn=lambda:score); t1=time.perf_counter_ns(); os.close(rd)
        return {'elapsed_ns':t1-t0,'periodic_samples':stats.samples,'records':len(s.rows),'agreement':summary['terminal_score_agreement']['agreement'],'final_callback_ns':final['sample_finished_ns']-final['sample_started_ns']}

def main():
    rows=[one() for _ in range(500)]; elapsed=[r['elapsed_ns'] for r in rows]; cb=[r['final_callback_ns'] for r in rows]
    out={'schema':'map01-finish-scorer-closure-benchmark-v1','environment':{'python':__import__('platform').python_version(),'kernel':__import__('platform').release(),'cpu_clock':'not pinned / unavailable','vizdoom_available':False},'workload':{'trials':500,'commands_per_trial':1,'command':'finish','game':'fake state mutated only inside finish callback'},'checks':{'all_agree':all(r['agreement'] for r in rows),'one_periodic_plus_one_final_record':all(r['periodic_samples']==1 and r['records']==2 for r in rows)},'elapsed_us':{'median':statistics.median(elapsed)/1e3,'p95':pct(elapsed,.95)/1e3,'p99':pct(elapsed,.99)/1e3,'max':max(elapsed)/1e3},'final_sample_callback_us':{'median':statistics.median(cb)/1e3,'p95':pct(cb,.95)/1e3,'p99':pct(cb,.99)/1e3,'max':max(cb)/1e3}}
    out['pass']=all(out['checks'].values()); print(json.dumps(out,indent=2)); raise SystemExit(0 if out['pass'] else 1)
if __name__=='__main__': main()
