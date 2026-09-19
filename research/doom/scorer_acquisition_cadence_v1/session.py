"""Versioned evaluator integration around immutable MAP01 v12/v13 components.

No API button selection, scorer-to-policy path, or runtime source edit. Every
provider call remains on the DoomGame-owning main thread. A one-tic refresh is an
explicit evaluator intervention and its wall blocking time is retained.
"""
from __future__ import annotations
import hashlib, json, os, sys, threading, time
from pathlib import Path
from acquisition import FinalAcquirer, validate_receipt

MODES = {'passive10': (10.0, False), 'refresh10': (10.0, True), 'refresh5': (5.0, True)}


def main():
    runtime = Path(os.environ['AI_RUNTIME_ROOT']).resolve()
    sys.path.insert(0, str(runtime / 'research/doom'))
    import session_map01_v12 as original
    import session_map01_v13 as components
    from doom_retained_input_backend_v3 import Backend
    from map01_scorer_stdio_adapter_v1 import MainThreadScorerStdin, ScorerFileSink

    out = Path(components._option('--out'))
    timeout = int(components._option('--timeout-seconds', '60'))
    if timeout < 10:
        raise ValueError('timeout must leave scoring slack')
    hz, refresh = MODES[os.environ['SCORER_MODE']]
    owner = threading.get_ident()
    holder, diagnostics = {}, []

    class Sink(ScorerFileSink):
        def __call__(self, receipt):
            validate_receipt(receipt)
            return super().__call__(receipt)
        def direct(self, *args):
            raise RuntimeError('pre-evaluated direct sample prohibited; use FinalAcquirer')

    sink = Sink(out)

    def sample_game():
        if threading.get_ident() != owner:
            raise RuntimeError('scorer left main owner thread')
        game = holder['game']
        if not game.initialized or game.closed:
            raise RuntimeError('sample outside initialized game lifetime')
        start = time.perf_counter_ns()
        before = int(game.get_episode_time())
        refresh_start = time.perf_counter_ns()
        called = refresh and not game.is_episode_finished()
        if called:
            game.advance_action(1, True)
        refresh_end = time.perf_counter_ns()
        sample = components._coherent_progress_sample(game, original.vd.GameVariable, timeout)
        after = int(game.get_episode_time())
        state = game.get_state()
        end = time.perf_counter_ns()
        diagnostics.append(dict(started_ns=start, finished_ns=end,
            thread_id=threading.get_ident(), refresh_called=called,
            refresh_started_ns=refresh_start, refresh_finished_ns=refresh_end,
            episode_tic_before=before, episode_tic_after=after,
            state_tic=None if state is None else int(state.tic), sample=sample.as_dict()))
        return sample

    final = FinalAcquirer(sample_game, sink)

    class Proxy(components._GameProxy):
        def close(self):
            if self.closed:
                return None
            try:
                if self.initialized:
                    self._final_sample()
            finally:
                self.closed = True
                self._inner.close()

    ctor0, stdin0, backend0 = original.vd.DoomGame, sys.stdin, original.Backend
    polling = MainThreadScorerStdin(stdin0, sample_game, sink, sample_hz=hz)

    def constructor(*args, **kwargs):
        holder['game'] = Proxy(ctor0(*args, **kwargs), final)
        return holder['game']

    original.vd.DoomGame, original.Backend, original.sys.stdin = constructor, Backend, polling
    try:
        original.main()
    finally:
        original.vd.DoomGame, original.Backend, original.sys.stdin = ctor0, backend0, stdin0
        sink.finalize(polling.stats())
        components._merge_sources(out)
        if out.exists():
            (out / 'acquisitions.jsonl').write_text(''.join(json.dumps(r, sort_keys=True)+'\n' for r in diagnostics))
            here = Path(__file__).resolve().parent
            provenance = {'mode': os.environ['SCORER_MODE'], 'sample_hz': hz,
                'owner_thread_id': owner, 'final_attempted': final.attempted,
                'sources': {n: hashlib.sha256((here/n).read_bytes()).hexdigest()
                            for n in ('session.py', 'acquisition.py')}}
            (out / 'candidate-sources.json').write_text(json.dumps(provenance, indent=2)+'\n')

if __name__ == '__main__':
    main()
