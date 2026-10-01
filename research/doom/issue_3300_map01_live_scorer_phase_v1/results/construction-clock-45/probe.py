from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

import vizdoom as vd
import sys
sys.path.insert(0, '/scorer')
from session_map01_v13 import _coherent_progress_sample

WAD = Path('/assets/freedoom2.wad')
OUT = Path(os.environ.get('OUT_NAME', '/results/raw-with-getter-trace.jsonl'))
EXPECTED_WAD = 'a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b'
SCORER = Path('/scorer/session_map01_v13.py')
ADAPTER = Path('/scorer/map01_scorer_stdio_adapter_v1.py')
SCORER_DEPS = ('main_thread_scorer_polling_v1.py', 'independent_progress_clock_v2.py')
GETTERS = {'get_episode_time', 'is_episode_finished', 'is_player_dead', 'get_game_variable', 'get_ticrate', 'is_episode_timeout_reached'}

class TimedProxy:
    def __init__(self, game):
        self.inner = game
        self.events = []
    def __getattr__(self, name):
        value = getattr(self.inner, name)
        if name not in GETTERS or not callable(value):
            return value
        def call(*args, **kwargs):
            start = time.monotonic_ns()
            result = value(*args, **kwargs)
            end = time.monotonic_ns()
            self.events.append({'name': name, 'args': [repr(a) for a in args],
                                'start_ns': start, 'end_ns': end,
                                'result': getattr(result, 'name', result), 'status': 'ok'})
            return result
        return call

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(index: int) -> dict:
    game = vd.DoomGame()
    row = {'schema': 'issue3453-construction-clock45-v1', 'index': index,
           'mode_requested': str(vd.Mode.ASYNC_SPECTATOR), 'ticrate_requested': 35,
           'wad_sha256': sha256(WAD), 'vizdoom_version': vd.__version__,
           'scorer_sha256': sha256(SCORER),
           'setup_status': 'not_started', 'scorer_status': 'not_called',
           'cleanup': {'game_closed': False}}
    try:
        game.set_doom_game_path(str(WAD))
        game.set_doom_map('map01')
        game.set_window_visible(False)
        game.set_sound_enabled(False)
        game.set_mode(vd.Mode.ASYNC_SPECTATOR)
        game.set_ticrate(35)
        game.set_available_buttons([])
        game.set_episode_timeout(350)
        game.set_seed(345300 + index)
        game.init()
        game.new_episode()
        row['setup_status'] = 'ok'
        row['mode_readback'] = str(game.get_mode())
        row['ticrate_readback'] = int(game.get_ticrate())
        row['buttons_readback'] = [str(x) for x in game.get_available_buttons()]
        row['episode_start_ns'] = time.monotonic_ns()
        row['passive_reads'] = []
        deadline = time.monotonic() + 1.5
        while time.monotonic() < deadline:
            before = time.monotonic_ns()
            try:
                tic = int(game.get_episode_time())
                status = 'ok'
            except BaseException as exc:
                tic, status = None, 'error'
                row['read_error'] = {'type': type(exc).__name__, 'message': str(exc)}
            after = time.monotonic_ns()
            row['passive_reads'].append({'start_ns': before, 'end_ns': after,
                                         'episode_tic': tic, 'status': status})
            time.sleep(.01)
        row['pre_scorer_ns'] = time.monotonic_ns()
        timed = TimedProxy(game)
        try:
            result = _coherent_progress_sample(timed, vd.GameVariable, 10.0)
            row['scorer_status'] = 'returned'
            row['scorer_return'] = result.as_dict()
        except BaseException as exc:
            row['scorer_status'] = 'raised'
            row['scorer_error'] = {'type': type(exc).__name__, 'message': str(exc)}
        row['post_scorer_ns'] = time.monotonic_ns()
        row['scorer_getter_trace'] = timed.events
        row['post_scorer_episode_tic'] = int(game.get_episode_time())
    except BaseException as exc:
        row['setup_status'] = 'STOP_SETUP_OR_INFRA'
        row['setup_error'] = {'type': type(exc).__name__, 'message': str(exc)}
    finally:
        try:
            game.close()
            row['cleanup']['game_closed'] = True
        except BaseException as exc:
            row['cleanup_error'] = {'type': type(exc).__name__, 'message': str(exc)}
        row['exit_ns'] = time.monotonic_ns()
        trace = Path('/tmp/vizdoom-tic-entry-v2.bin')
        row['trace_exists'] = trace.is_file()
        if trace.is_file():
            data = trace.read_bytes()
            record_size = 24
            records = [list(__import__('struct').unpack_from('<QQii', data, i))
                       for i in range(0, len(data) - record_size + 1, record_size)]
            row['tic_entry_records'] = records
            row['trace_sha256'] = hashlib.sha256(data).hexdigest()
        with OUT.open('a', encoding='utf-8') as f:
            f.write(json.dumps(row, sort_keys=True) + '\n')
            f.flush()
            os.fsync(f.fileno())
    return row

def main() -> None:
    if sha256(WAD) != EXPECTED_WAD:
        raise SystemExit('STOP_SETUP_OR_INFRA: WAD hash mismatch')
    if not SCORER.is_file() or not ADAPTER.is_file() or any(not (Path('/scorer') / name).is_file() for name in SCORER_DEPS):
        raise SystemExit('STOP_SETUP_OR_INFRA: exact current-main scorer dependency missing')
    results = [run(i + 3) for i in range(3)]
    print(json.dumps({'rows': len(results), 'setup_ok': sum(x['setup_status'] == 'ok' for x in results),
                      'scorer_returned': sum(x['scorer_status'] == 'returned' for x in results),
                      'clean': sum(x['cleanup']['game_closed'] for x in results)}, sort_keys=True))

if __name__ == '__main__':
    main()
