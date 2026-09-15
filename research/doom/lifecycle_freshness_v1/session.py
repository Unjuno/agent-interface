"""Real MAP01 lifecycle-freshness fault-injection experiment.

Only delivery to the optional lifecycle gate is faulted. Scorer acquisition still
records the actual engine state off-policy. Silence never cancels active input.
"""
from __future__ import annotations
import hashlib,json,os,sys,threading,time,uuid
from pathlib import Path
from acquisition import FinalAcquirer, validate_receipt
from gate import LifecycleGate, observe_and_cancel
from monitor import KeymapMonitor


def main():
    runtime=Path(os.environ['AI_RUNTIME_ROOT']).resolve()
    sys.path.insert(0,str(runtime/'research/doom'))
    import session_map01_v12 as base
    import session_map01_v13 as components
    from doom_retained_input_backend_v3 import Backend as PriorBackend
    from map01_scorer_stdio_adapter_v1 import MainThreadScorerStdin, ScorerFileSink
    out=Path(components._option('--out')); timeout=int(components._option('--timeout-seconds','60'))
    freshness_ms=int(os.environ.get('LIFECYCLE_FRESHNESS_MS','0'))
    freshness_ns=None if freshness_ms == 0 else freshness_ms*1_000_000
    fault=os.environ.get('LIFECYCLE_FAULT','none')
    delay_ms=int(os.environ.get('LIFECYCLE_DELAY_MS','0'))
    if fault not in {'none','drop_terminal','delay_terminal'}: raise ValueError('unsupported lifecycle fault')
    if fault=='delay_terminal' and delay_ms <= 0: raise ValueError('positive delay required')
    owner=threading.get_ident(); epoch=uuid.uuid4().hex; holder={}; diagnostics=[]
    gate=LifecycleGate(epoch,freshness_ns)
    pending_terminal=None; terminal_delivered=False

    class Backend(PriorBackend):
        def __init__(self,session,*args,**kwargs):
            super().__init__(session,*args,**kwargs)
            holder['monitor']=KeymapMonitor(session.name,out/'keymap.jsonl'); holder['backend']=self
        def close(self):
            try:return super().close()
            finally:
                if 'monitor' in holder: holder.pop('monitor').close()

    executor0=base.Executor
    class Executor(executor0):
        def __init__(self,*args,**kwargs): super().__init__(*args,**kwargs); holder['executor']=self
        def submit(self,*args,**kwargs):
            with self.lock:
                gate.require_open(epoch,now_ns=time.perf_counter_ns())
                return super().submit(*args,**kwargs)

    class Sink(ScorerFileSink):
        def __call__(self,receipt): validate_receipt(receipt); return super().__call__(receipt)
        def direct(self,*args): raise RuntimeError('pre-evaluated final receipt forbidden')
    sink=Sink(out)

    def sample_game():
        nonlocal pending_terminal,terminal_delivered
        if threading.get_ident()!=owner: raise RuntimeError('game getter left owner thread')
        game=holder['game']
        if not game.initialized or game.closed: raise RuntimeError('sample outside game lifetime')
        start=time.perf_counter_ns(); before=int(game.get_episode_time())
        refresh_start=time.perf_counter_ns(); called=not game.is_episode_finished()
        if called: game.advance_action(1,True)
        refresh_end=time.perf_counter_ns()
        sample=components._coherent_progress_sample(game,base.vd.GameVariable,timeout)
        after=int(game.get_episode_time()); timed_out=bool(game.is_episode_timeout_reached()); end=time.perf_counter_ns()
        seq=len(diagnostics)
        row=dict(started_ns=start,finished_ns=end,thread_id=owner,refresh_called=called,
                 refresh_started_ns=refresh_start,refresh_finished_ns=refresh_end,
                 episode_tic_before=before,episode_tic_after=after,timeout_reached=timed_out,
                 sample=sample.as_dict(),epoch=epoch,sequence=seq,fault=fault,lifecycle_delivery='none')
        if sample.episode_finished and pending_terminal is None and not terminal_delivered:
            pending_terminal=dict(sequence=seq,observed_ns=end)
        if not sample.episode_finished:
            delivered=time.perf_counter_ns()
            row.update(observe_and_cancel(holder['executor'],gate,epoch=epoch,sequence=seq,
                ended=False,observed_ns=end,delivered_ns=delivered)); row['lifecycle_delivery']='running'
        elif fault=='none' and not terminal_delivered:
            delivered=time.perf_counter_ns()
            row.update(observe_and_cancel(holder['executor'],gate,epoch=epoch,sequence=seq,
                ended=True,observed_ns=end,delivered_ns=delivered)); row['lifecycle_delivery']='terminal'; terminal_delivered=True
        elif fault=='delay_terminal' and not terminal_delivered:
            assert pending_terminal is not None
            if end-pending_terminal['observed_ns'] >= delay_ms*1_000_000:
                delivered=time.perf_counter_ns()
                row.update(observe_and_cancel(holder['executor'],gate,epoch=epoch,
                    sequence=pending_terminal['sequence'],ended=True,observed_ns=pending_terminal['observed_ns'],
                    delivered_ns=delivered)); row['lifecycle_delivery']='terminal_delayed'; terminal_delivered=True
        elif fault=='drop_terminal':
            row['lifecycle_delivery']='suppressed_after_terminal'
        diagnostics.append(row)
        return sample

    final=FinalAcquirer(sample_game,sink)
    class Proxy(components._GameProxy):
        def close(self):
            if self.closed:return None
            try:
                if self.initialized:self._final_sample()
            finally:
                self.closed=True;self._inner.close()

    ctor0,stdin0,backend0=base.vd.DoomGame,sys.stdin,base.Backend
    polling=MainThreadScorerStdin(stdin0,sample_game,sink,sample_hz=10.0)
    def ctor(*args,**kwargs): holder['game']=Proxy(ctor0(*args,**kwargs),final); return holder['game']
    base.vd.DoomGame,base.Backend,base.Executor,base.sys.stdin=ctor,Backend,Executor,polling
    try:base.main()
    finally:
        base.vd.DoomGame,base.Backend,base.Executor,base.sys.stdin=ctor0,backend0,executor0,stdin0
        if 'monitor' in holder:holder.pop('monitor').close()
        sink.finalize(polling.stats());components._merge_sources(out)
        if out.exists():
            (out/'acquisitions.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in diagnostics))
            here=Path(__file__).resolve().parent
            (out/'candidate-sources.json').write_text(json.dumps(dict(epoch=epoch,owner_thread_id=owner,
                freshness_ms=freshness_ms,fault=fault,delay_ms=delay_ms,final_attempted=final.attempted,
                gate=dict(sequence=gate.sequence,observed_ns=gate.observed_ns,ended=gate.ended,first_end_ns=gate.first_end_ns),
                sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in here.glob('*.py')}),indent=2)+'\n')

if __name__=='__main__':main()
