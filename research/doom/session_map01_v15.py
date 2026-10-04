"""MAP01 v15 cleanup successor for the retained v14 measurement source.

This version fixes scorer-failure cleanup in the game proxy. It is a source-level
successor only; it does not alter the frozen v14 evidence or authorize a run.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

from independent_progress_clock_v2 import ProgressSample
from map01_scorer_stdio_adapter_v1 import MainThreadScorerStdin, ScorerFileSink

HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parent


def _option(name, default=None):
    args = sys.argv[1:]
    if name not in args:
        if default is not None:
            return default
        raise ValueError(f"required option missing: {name}")
    i = args.index(name)
    if i + 1 >= len(args):
        raise ValueError("option requires value: " + name)
    return args[i + 1]


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _merge_sources(out):
    path = Path(out) / "sources.json"
    if not path.exists():
        return False
    data = json.loads(path.read_text(encoding="utf-8"))
    additions = [HERE / "session_map01_v15.py",
                 HERE / "map01_scorer_stdio_adapter_v1.py",
                 HERE / "main_thread_scorer_polling_v1.py",
                 HERE / "independent_progress_clock_v2.py",
                 HERE / "doom_retained_input_backend_v5.py",
                 RESEARCH / "live_control/input_transition_owner_v4.py",
                 RESEARCH / "live_control/input_owner_v12.py"]
    for source in additions:
        data[str(source.relative_to(RESEARCH))] = _sha(source)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    return True


def _coherent_progress_sample(game, game_variable, timeout_seconds,
                               clock_ns=time.perf_counter_ns, attempts=3):
    """Read scorer state only when all fields are bracketed by one episode tic."""
    if type(attempts) is not int or attempts < 1:
        raise ValueError("attempts must be positive integer")
    for _ in range(attempts):
        tic_before = int(game.get_episode_time())
        finished = bool(game.is_episode_finished())
        dead = bool(game.is_player_dead())
        kills = int(game.get_game_variable(game_variable.KILLCOUNT))
        deaths = int(game.get_game_variable(game_variable.DEATHCOUNT))
        ticrate = int(game.get_ticrate())
        timeout_method = getattr(game, "is_episode_timeout_reached", None)
        timeout_reached = (bool(timeout_method()) if callable(timeout_method)
                           else tic_before >= timeout_seconds * ticrate)
        tic_after = int(game.get_episode_time())
        if tic_before == tic_after:
            return ProgressSample(clock_ns(), kills, deaths, finished, dead,
                                  bool(finished and not dead and not timeout_reached))
    raise RuntimeError("independent scorer could not obtain one-tic coherent sample")


class _GameProxy:
    def __init__(self, inner, final_sample):
        self._inner = inner
        self._final_sample = final_sample
        self.initialized = False
        self.closed = False

    def __getattr__(self, name):
        return getattr(self._inner, name)

    def init(self):
        result = self._inner.init()
        self.initialized = True
        return result

    def close(self):
        sample_error = None
        sample_traceback = None
        if self.initialized and not self.closed:
            try:
                self._final_sample()
            except BaseException as exc:
                sample_error = exc
                sample_traceback = exc.__traceback__

        close_error = None
        close_traceback = None
        result = None
        try:
            result = self._inner.close()
        except BaseException as exc:
            close_error = exc
            close_traceback = exc.__traceback__
        finally:
            self.closed = True

        if sample_error is not None:
            raise sample_error.with_traceback(sample_traceback) from close_error
        if close_error is not None:
            raise close_error.with_traceback(close_traceback)
        return result


def main():
    out = Path(_option("--out"))
    timeout_seconds = int(_option("--timeout-seconds", "600"))
    if timeout_seconds < 10:
        raise ValueError("timeout must leave scoring slack")
    import session_map01_v12 as base
    from doom_retained_input_backend_v5 import Backend as TelemetryBackend

    holder = {}
    sink = ScorerFileSink(out)

    def sample_game():
        game = holder.get("game")
        if game is None or not game.initialized or game.closed:
            raise RuntimeError("scorer sampled outside initialized game lifetime")
        return _coherent_progress_sample(game, base.vd.GameVariable, timeout_seconds)

    def final_sample():
        sink.direct(sample_game(), time.perf_counter_ns)

    original_ctor = base.vd.DoomGame
    original_stdin = sys.stdin
    polling = MainThreadScorerStdin(original_stdin, sample_game, sink, sample_hz=35.0)

    def ctor(*args, **kwargs):
        proxy = _GameProxy(original_ctor(*args, **kwargs), final_sample)
        holder["game"] = proxy
        return proxy

    base.vd.DoomGame = ctor
    base.Backend = TelemetryBackend
    base.sys.stdin = polling
    try:
        base.main()
    finally:
        base.vd.DoomGame = original_ctor
        base.sys.stdin = original_stdin
        sink.finalize(polling.stats())
        _merge_sources(out)


if __name__ == "__main__":
    main()
