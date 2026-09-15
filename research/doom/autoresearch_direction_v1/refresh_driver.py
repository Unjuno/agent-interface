"""Matched passive/refresh1 diagnostic using the identical frozen X11 runner."""
import argparse, json, statistics
from pathlib import Path
import runner

def run(spec, allocation):
    original=runner.subprocess.Popen
    def launch(args,*pos,**kw):
        if len(args)>1 and str(args[1]).endswith('/session_map01_v13.py'):
            args=list(args);args[1]=str(runner.HERE/'trace_session.py')
            kw['env']=dict(kw.get('env') or {});kw['env']['SCORER_REFRESH_MODE']=spec['mode']
        return original(args,*pos,**kw)
    runner.subprocess.Popen=launch
    out=runner.ROOT/'evidence'/allocation/spec['id']
    try:r=runner.run_case(spec,out)
    finally:runner.subprocess.Popen=original
    trace=runner.rows(out/'runtime/evaluator-trace.jsonl')
    refresh=[(x['refresh_finished_ns']-x['refresh_started_ns'])/1e6 for x in trace if x['refresh_called']]
    ticks=[x['episode_tic_after'] for x in trace]
    owner=json.loads((out/'runtime/evaluator-provenance.json').read_text())['owner_thread_id']
    r.update(mode=spec['mode'],evaluator_tick_unique=len(set(ticks)),
      evaluator_tick_first=ticks[0],evaluator_tick_last=ticks[-1],
      acquisition_brackets_valid=all(x['started_ns']<=x['sample']['sample_ns']<=x['finished_ns'] for x in trace),
      owner_thread_consistent=all(x['thread_id']==owner for x in trace),
      refresh_duration_ms={'median':statistics.median(refresh),'min':min(refresh),'max':max(refresh)} if refresh else None)
    runner.dump(out/'analysis.json',r)
    if not r['acquisition_brackets_valid'] or not r['owner_thread_consistent']:raise RuntimeError('evaluator contract')
    print(json.dumps(r),flush=True)
    return r

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--plan',type=Path);ap.add_argument('--pair',type=int);ap.add_argument('--preflight',action='store_true');a=ap.parse_args()
    if a.preflight:
        spec={'id':'refresh-preflight','fixture':str(runner.FIXTURE),'seed':997299,'policy':'attack','cutoff_ms':250,'state':'original','rep':0,'mode':'refresh1'}
        run(spec,'refresh-preflight');return
    plan=json.loads(a.plan.read_text())
    for n,h in plan['source_sha256'].items():
        if runner.sha(runner.HERE/n)!=h:raise RuntimeError('source changed '+n)
    for spec in plan['cases']:
        if spec['rep']!=a.pair:continue
        if runner.sha(Path(spec['fixture']))!=spec['fixture_sha256']:raise RuntimeError('fixture changed')
        run(spec,plan['allocation'])
if __name__=='__main__':main()
