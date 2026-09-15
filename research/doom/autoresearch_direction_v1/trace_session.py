"""Versioned evaluator refresh probe; never selects actions or emits scorer to policy.

Both modes sample at 10 Hz. Only refresh1 requests a one-tic engine state update.
Historical runtime bytes remain untouched; measured adapter hashes are separate.
"""
from __future__ import annotations
import hashlib,json,os,sys,threading,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
RUNTIME=HERE.parents[2]/'runtime'
sys.path.insert(0,str(RUNTIME/'research/doom'))
import session_map01_v13 as base


def main():
    mode=os.environ['SCORER_REFRESH_MODE']
    if mode not in ('passive','refresh1'):raise ValueError('unknown sampling mode')
    out=Path(sys.argv[sys.argv.index('--out')+1]);owner=threading.get_ident();trace=[]
    orig_sample=base._coherent_progress_sample;orig_stdin=base.MainThreadScorerStdin
    class TenHzStdin(orig_stdin):
        def __init__(self,*args,**kwargs):
            kwargs['sample_hz']=10.0
            super().__init__(*args,**kwargs)
    def traced(game,variables,timeout_seconds):
        if threading.get_ident()!=owner:raise RuntimeError('scorer left owner thread')
        started=time.perf_counter_ns();tic_before=int(game.get_episode_time())
        refresh_started=time.perf_counter_ns();refresh_called=False
        if mode=='refresh1' and not game.is_episode_finished():
            # ASYNC_SPECTATOR consumes only existing OS input; no set_action/make_action.
            game.advance_action(1,True);refresh_called=True
        refreshed=time.perf_counter_ns()
        sample=orig_sample(game,variables,timeout_seconds)
        tic_after=int(game.get_episode_time());state=game.get_state()
        health=game.get_game_variable(variables.HEALTH);ammo=game.get_game_variable(variables.AMMO2)
        finished=time.perf_counter_ns()
        trace.append({'mode':mode,'thread_id':threading.get_ident(),'started_ns':started,
          'finished_ns':finished,'refresh_called':refresh_called,'refresh_started_ns':refresh_started,
          'refresh_finished_ns':refreshed,'episode_tic_before':tic_before,'episode_tic_after':tic_after,
          'state_tic':None if state is None else state.tic,'health':health,'ammo':ammo,'sample':sample.as_dict()})
        return sample
    base._coherent_progress_sample=traced;base.MainThreadScorerStdin=TenHzStdin
    try:base.main()
    finally:
        base._coherent_progress_sample=orig_sample;base.MainThreadScorerStdin=orig_stdin
        if out.exists():
            (out/'evaluator-trace.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in trace))
            data={'mode':mode,'sample_hz':10,'owner_thread_id':owner,'no_action_selection_api':True,
                  'source_sha256':{Path(__file__).name:hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}}
            (out/'evaluator-provenance.json').write_text(json.dumps(data,indent=2)+'\n')
if __name__=='__main__':main()
