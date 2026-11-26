import json
import math
import os
import time
from pathlib import Path

import vizdoom as vd


def synchronize_terminal(game, out, physical_neutral, verify_owner, *, deadline_ns,
                         clock=time.perf_counter_ns):
    """Record one bounded synchronization request, without retrying it."""
    path = Path(out) / 'synthetic-terminal-refresh.jsonl'
    with path.open('x', encoding='utf-8') as log:
        def record(event, **data):
            log.write(json.dumps({'event': event, 'time_ns': clock(), **data}) + '\n')
            log.flush()
            os.fsync(log.fileno())

        def sample():
            before_tic = game.get_episode_time()
            finished = game.is_episode_finished()
            dead = game.is_player_dead()
            timeout = game.is_episode_timeout_reached()
            deaths = game.get_game_variable(vd.GameVariable.DEATHCOUNT)
            action = list(game.get_last_action())
            after_tic = game.get_episode_time()
            if (type(before_tic) is not int or type(after_tic) is not int or before_tic < 0 or before_tic != after_tic
                    or any(type(v) is not bool for v in (finished, dead, timeout))
                    or type(deaths) not in (int, float) or not math.isfinite(deaths)
                    or deaths < 0 or deaths % 1 != 0 or len(action) != 9
                    or any(type(v) not in (int, float) or not math.isfinite(v) for v in action)):
                raise ValueError('terminal state is not coherent and neutral')
            return {'tic': before_tic, 'finished': finished, 'dead': dead,
                    'native_timeout': timeout, 'deaths': deaths, 'last_action': action}

        if type(deadline_ns) is not int or clock() >= deadline_ns:
            raise ValueError('synchronization deadline expired')
        owner = verify_owner()
        if type(owner) is not dict or owner.get('verified') is not True or physical_neutral() is not True:
            raise ValueError('neutral input custody is not verified')
        before = sample()
        record('before', sample=before, owner=owner)
        if before['dead'] or before['native_timeout'] or before['deaths'] != 0 or clock() >= deadline_ns:
            raise ValueError('terminal state is late or cannot distinguish exit')
        if before['finished']:
            record('already_finished')
            return {'disposition': 'already_finished', 'before': before, 'refresh_calls': 0}
        if before['deaths'] != 0 or any(value != 0 for value in before['last_action']):
            raise ValueError('engine state does not permit neutral synchronization')
        if physical_neutral() is not True or clock() >= deadline_ns:
            raise ValueError('neutrality or deadline expired')
        record('attempt')
        pre_call = sample()
        neutral_pre_call = physical_neutral() is True
        if (clock() >= deadline_ns or not neutral_pre_call or pre_call['dead']
                or pre_call['native_timeout'] or pre_call['deaths'] != 0):
            record('pre_call', sample=pre_call, physical_neutral=neutral_pre_call)
            raise ValueError('synchronization prerequisites changed before call')
        if pre_call['finished']:
            record('pre_call', sample=pre_call, physical_neutral=neutral_pre_call)
            record('already_finished_before_call')
            return {'disposition': 'already_finished', 'before': before,
                    'pre_call': pre_call, 'refresh_calls': 0}
        if any(value != 0 for value in pre_call['last_action']):
            record('pre_call', sample=pre_call, physical_neutral=neutral_pre_call)
            raise ValueError('engine input changed before call')
        pre_call_recorded = False
        try:
            game.advance_action(1, True)
            returned_ns = clock()
            record('pre_call', sample=pre_call, physical_neutral=neutral_pre_call)
            pre_call_recorded = True
            record('returned', returned_ns=returned_ns)
            after = sample()
            neutral_after = physical_neutral() is True
            sampled_ns = clock()
            record('after', sample=after, physical_neutral=neutral_after, sampled_ns=sampled_ns)
            if not neutral_after or sampled_ns >= deadline_ns or after['dead'] or after['native_timeout'] or after['deaths'] != 0:
                raise ValueError('synchronization result is late or inconclusive')
        except Exception as error:
            if not pre_call_recorded:
                record('pre_call', sample=pre_call, physical_neutral=neutral_pre_call)
            record('error', error_type=type(error).__name__)
            raise
        return {'disposition': 'refreshed', 'before': before, 'after': after, 'refresh_calls': 1}
