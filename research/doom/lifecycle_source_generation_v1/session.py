"""Real MAP01 experiment separating receipt freshness from source-generation freshness."""
from __future__ import annotations
import hashlib,json,os,sys,threading,time,uuid
from pathlib import Path
from acquisition import FinalAcquirer,validate_receipt
from gate import LifecycleGate,observe_and_cancel
from monitor import KeymapMonitor

def main():
    runtime=Path(os.environ['AI_RUNTIME_ROOT']).resolve();sys.path.insert(0,str(runtime/'research/doom'))
    import session_map01_v12 as base
    import session_map01_v13 as components
    from doom_retained_input_backend_v3 import Backend as PriorBackend
    from map01_scorer_stdio_adapter_v1 import MainThreadScorerStdin,ScorerFileSink
    out=Path(components._option('--out'));timeout=int(components._option('--timeout-seconds','60'))
    delivery_ms=int(os.environ.get('LIFECYCLE_DELIVERY_FRESHNESS_MS','300'))
    progress_ms=int(os.environ.get('LIFECYCLE_SOURCE_PROGRESS_MS','0'))
    progress_ns=None if progress_ms==0 else progress_ms*1_000_000
    fault=os.environ.get('LIFECYCLE_FAULT','none')
    if fault not in {'none','false_running_after_terminal'}:raise ValueError('unsupported lifecycle fault')
    owner=threading.get_ident();epoch=uuid.uuid4().hex;holder={};diagnostics=[]
    gate=LifecycleGate(epoch,delivery_ms*1_000_000,progress_ns)

    class Backend(PriorBackend):
        def __init__(self,session,*args,**kwargs):
            super().__init__(session,*args,**kwargs);holder['monitor']=KeymapMonitor(session.name,out/'keymap.jsonl');holder['backend']=self
        def close(self):
            try:return super().close()
            finally:
                if 'monitor' in holder:holder.pop('monitor').close()
    executor0=base.Executor
    class Executor(executor0):
        def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);holder['executor']=self
        def submit(self,*args,**kwargs):
            with self.lock:
                gate.require_open(epoch,now_ns=time.perf_counter_ns());return super().submit(*args,**kwargs)
    class Sink(ScorerFileSink):
        def __call__(self,receipt):validate_receipt(receipt);return super().__call__(receipt)
        def direct(self,*args):raise RuntimeError('pre-evaluated final receipt forbidden')
    sink=Sink(out)

    def sample_game():
        if threading.get_ident()!=owner:raise RuntimeError('game getter left owner thread')
        game=holder['game']
        if not game.initialized or game.closed:raise RuntimeError('sample outside game lifetime')
        start=time.perf_counter_ns();before=int(game.get_episode_time());called=not game.is_episode_finished()
        rs=time.perf_counter_ns()
        if called:game.advance_action(1,True)
        re=time.perf_counter_ns();sample=components._coherent_progress_sample(game,base.vd.GameVariable,timeout)
        after=int(game.get_episode_time());timed_out=bool(game.is_episode_timeout_reached());end=time.perf_counter_ns();seq=len(diagnostics)
        actual_ended=bool(sample.episode_finished);delivered_ended=actual_ended
        delivery='terminal' if actual_ended else 'running'
        if fault=='false_running_after_terminal' and actual_ended:
            delivered_ended=False;delivery='false_running_after_terminal'
        delivered=time.perf_counter_ns()
        row=dict(started_ns=start,finished_ns=end,thread_id=owner,refresh_called=called,
            refresh_started_ns=rs,refresh_finished_ns=re,episode_tic_before=before,episode_tic_after=after,
            source_generation=after,timeout_reached=timed_out,sample=sample.as_dict(),epoch=epoch,sequence=seq,
            fault=fault,lifecycle_delivery=delivery,delivered_ended=delivered_ended)
        row.update(observe_and_cancel(holder['executor'],gate,epoch=epoch,sequence=seq,ended=delivered_ended,
            observed_ns=end,source_generation=after,delivered_ns=delivered))
        diagnostics.append(row);return sample

    final=FinalAcquirer(sample_game,sink)
    class Proxy(components._GameProxy):
        def close(self):
            if self.closed:return None
            try:
                if self.initialized:self._final_sample()
            finally:self.closed=True;self._inner.close()
    ctor0,stdin0,backend0=base.vd.DoomGame,sys.stdin,base.Backend
    polling=MainThreadScorerStdin(stdin0,sample_game,sink,sample_hz=10.0)
    def ctor(*args,**kwargs):holder['game']=Proxy(ctor0(*args,**kwargs),final);return holder['game']
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
              delivery_freshness_ms=delivery_ms,source_progress_freshness_ms=progress_ms,fault=fault,
              final_attempted=final.attempted,gate=dict(sequence=gate.sequence,observed_ns=gate.observed_ns,
              ended=gate.ended,first_end_ns=gate.first_end_ns,source_generation=gate.source_generation,
              source_advanced_ns=gate.source_advanced_ns),sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in here.glob('*.py')}),indent=2)+'\n')
if __name__=='__main__':main()
