"""Finite provider-lifecycle experiment around immutable MAP01 components.

Engine getters stay on owner main thread. Lifecycle can only revoke, never
choose inputs. This optional capability is NOT screenshot-only gameplay.
"""
from __future__ import annotations
import hashlib, json, os, sys, threading, time, uuid
from pathlib import Path
from acquisition import FinalAcquirer, validate_receipt
from monitor import KeymapMonitor


def main():
    runtime=Path(os.environ['AI_RUNTIME_ROOT']).resolve()
    sys.path.insert(0,str(runtime/'research/doom'))
    import session_map01_v12 as base
    import session_map01_v13 as components
    from doom_retained_input_backend_v3 import Backend as PriorBackend
    from map01_scorer_stdio_adapter_v1 import MainThreadScorerStdin, ScorerFileSink
    enabled=os.environ.get('LIFECYCLE_GUARD','0')=='1'
    out=Path(components._option('--out')); timeout=int(components._option('--timeout-seconds','60'))
    owner=threading.get_ident(); epoch=uuid.uuid4().hex; holder={}; diagnostics=[]
    gate=None
    if enabled:
        from gate import TerminalGate, observe_and_cancel
        gate=TerminalGate(epoch)

    class Backend(PriorBackend):
        def __init__(self, session, *args, **kwargs):
            super().__init__(session,*args,**kwargs)
            holder['monitor']=KeymapMonitor(session.name,out/'keymap.jsonl')
            holder['backend']=self
        def close(self):
            try: return super().close()
            finally:
                if 'monitor' in holder: holder.pop('monitor').close()

    executor0=base.Executor
    class Executor(executor0):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs); holder['executor']=self
        def submit(self,*args,**kwargs):
            with self.lock:
                if gate is not None: gate.require_open(epoch)
                return super().submit(*args,**kwargs)

    class Sink(ScorerFileSink):
        def __call__(self,receipt):
            validate_receipt(receipt); return super().__call__(receipt)
        def direct(self,*args): raise RuntimeError('pre-evaluated final receipt forbidden')
    sink=Sink(out)

    def sample_game():
        if threading.get_ident()!=owner: raise RuntimeError('game getter left owner thread')
        game=holder['game']
        if not game.initialized or game.closed: raise RuntimeError('sample outside game lifetime')
        start=time.perf_counter_ns(); before=int(game.get_episode_time())
        refresh_start=time.perf_counter_ns(); called=not game.is_episode_finished()
        if called: game.advance_action(1,True)
        refresh_end=time.perf_counter_ns()
        sample=components._coherent_progress_sample(game,base.vd.GameVariable,timeout)
        after=int(game.get_episode_time()); timed_out=bool(game.is_episode_timeout_reached())
        end=time.perf_counter_ns()
        row=dict(started_ns=start,finished_ns=end,thread_id=owner,
                 refresh_called=called,refresh_started_ns=refresh_start,refresh_finished_ns=refresh_end,
                 episode_tic_before=before,episode_tic_after=after,timeout_reached=timed_out,
                 sample=sample.as_dict(),epoch=epoch,sequence=len(diagnostics))
        diagnostics.append(row)
        # Only an epoch-bound terminal bit crosses the optional capability boundary.
        # No score/health/ammo/reason enters the action choice or controller channel.
        if gate is not None:
            row.update(observe_and_cancel(holder['executor'],gate,epoch=epoch,
                sequence=row['sequence'],ended=sample.episode_finished,observed_ns=end))
        return sample

    final=FinalAcquirer(sample_game,sink)
    class Proxy(components._GameProxy):
        def close(self):
            if self.closed: return None
            try:
                if self.initialized: self._final_sample()
            finally:
                self.closed=True; self._inner.close()

    ctor0,stdin0,backend0=base.vd.DoomGame,sys.stdin,base.Backend
    polling=MainThreadScorerStdin(stdin0,sample_game,sink,sample_hz=10.0)
    def ctor(*args,**kwargs):
        holder['game']=Proxy(ctor0(*args,**kwargs),final); return holder['game']
    base.vd.DoomGame,base.Backend,base.Executor,base.sys.stdin=ctor,Backend,Executor,polling
    try: base.main()
    finally:
        base.vd.DoomGame,base.Backend,base.Executor,base.sys.stdin=ctor0,backend0,executor0,stdin0
        if 'monitor' in holder: holder.pop('monitor').close()
        sink.finalize(polling.stats()); components._merge_sources(out)
        if out.exists():
            (out/'acquisitions.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in diagnostics))
            here=Path(__file__).resolve().parent
            (out/'candidate-sources.json').write_text(json.dumps(dict(guard=enabled,epoch=epoch,
                owner_thread_id=owner,final_attempted=final.attempted,
                sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in here.glob('*.py')}),indent=2)+'\n')

if __name__=='__main__': main()
