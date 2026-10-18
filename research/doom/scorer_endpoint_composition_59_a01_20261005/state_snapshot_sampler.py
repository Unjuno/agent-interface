"""Candidate V16 sample function backed by one coherent GameState vector."""
from __future__ import annotations

import math
import time
from numbers import Real

from independent_progress_clock_v2 import ProgressSample


def coherent_snapshot_sample(game, game_variable, timeout_seconds,
                             clock_ns=time.perf_counter_ns, attempts=3):
    """Return one sample only when counters and game predicates share a tic.

    This can be supplied as ``AcknowledgedSampler.sample_fn``. The enclosing
    sampler still owns the advance_action acknowledgment and producer receipt.
    """
    if type(attempts) is not int or attempts < 1:
        raise ValueError("attempts must be a positive integer")
    available = list(game.get_available_game_variables())
    required = (game_variable.KILLCOUNT, game_variable.DEATHCOUNT)
    indexes = []
    for variable in required:
        found = [index for index, configured in enumerate(available)
                 if configured == variable]
        if len(found) != 1:
            raise ValueError("kill/death counters must each be configured once")
        indexes.append(found[0])

    for _ in range(attempts):
        tic_before = game.get_episode_time()
        state = game.get_state()
        finished = bool(game.is_episode_finished())
        dead = bool(game.is_player_dead())
        ticrate = game.get_ticrate()
        timeout_method = getattr(game, "is_episode_timeout_reached", None)
        timeout_reached = (bool(timeout_method()) if callable(timeout_method)
                           else tic_before >= timeout_seconds * ticrate)
        tic_after = game.get_episode_time()
        if (type(tic_before) is not int or type(tic_after) is not int or
                tic_before < 0 or tic_after < 0):
            raise ValueError("invalid episode tic")
        if type(getattr(state, "tic", None)) is not int or state.tic < 0:
            raise ValueError("invalid GameState tic")
        if tic_before != tic_after or state is None or state.tic != tic_after:
            continue
        raw_values = state.game_variables
        if len(raw_values) != len(available):
            raise ValueError("GameState variable vector does not match configuration")
        counters = []
        for index in indexes:
            value = raw_values[index]
            if isinstance(value, bool) or not isinstance(value, Real):
                raise ValueError("invalid score counter")
            numeric = float(value)
            if not math.isfinite(numeric) or not numeric.is_integer() or numeric < 0:
                raise ValueError("invalid score counter")
            counters.append(int(numeric))
        sample = ProgressSample(
            clock_ns(), counters[0], counters[1], finished, dead,
            bool(finished and not dead and not timeout_reached))
        sample.validate()
        return sample
    raise RuntimeError("no GameState snapshot matched the acknowledged endpoint")
