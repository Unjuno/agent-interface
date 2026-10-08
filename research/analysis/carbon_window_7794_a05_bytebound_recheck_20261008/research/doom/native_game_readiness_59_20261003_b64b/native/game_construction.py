"""Two bounded native game construction cells; literal controller, hidden scorer."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time
import traceback

import vizdoom as vd
from Xlib import X, XK, display
from PIL import ImageGrab
from input_transition_owner_v3 import InputOwner
from lease import Lease

OUT = Path('/out')
IMAGE = 'sha256:93ef9169b70d152291972b652bde109d15868d25f65e1110a817b1f63ead886f'


def write(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2, sort_keys=True)
        f.write('\n')


def cell(kind):
    out = OUT / kind
    out.mkdir()
    result = {'kind': kind, 'utc_start': datetime.now(timezone.utc).isoformat(),
              'seed': 7, 'action': 'none' if kind == 'control' else 'Space1000ms',
              'events': [], 'privileged_samples': [], 'cleanup': []}
    xproc = game = owner = connection = None
    resource.setrlimit(resource.RLIMIT_FSIZE, (8 << 20, 8 << 20))
    try:
        name = ':81'
        os.environ.update(DISPLAY=name, SDL_VIDEODRIVER='x11',
                          HOME='/tmp/home-' + kind,
                          XDG_CONFIG_HOME='/tmp/home-' + kind,
                          SDL_AUDIODRIVER='dummy')
        os.environ.pop('WAYLAND_DISPLAY', None)
        Path(os.environ['HOME']).mkdir()
        xlog = (out / 'xvfb.log').open('wb')
        xproc = subprocess.Popen(['Xvfb', name, '-screen', '0', '800x600x24',
                                  '-nolisten', 'tcp', '-ac', '-noreset'],
                                 stdout=xlog, stderr=subprocess.STDOUT)
        ready_until = time.monotonic() + 3
        while time.monotonic() < ready_until:
            if xproc.poll() is not None:
                raise RuntimeError('Xvfb exited')
            try:
                connection = display.Display(name)
                break
            except Exception:
                time.sleep(.02)
        if connection is None:
            raise RuntimeError('X11 handshake timeout')
        result['xvfb_pid'] = xproc.pid
        root = connection.screen().root
        package = Path(vd.__file__).parent
        config = Path('/tmp') / ('game-' + kind + '.ini')
        config.write_text('[Doom.Bindings]\nspace=+attack\n')
        game = vd.DoomGame()
        game.load_config(str(package / 'scenarios/basic.cfg'))
        game.set_doom_config_path(str(config))
        game.set_mode(vd.Mode.ASYNC_SPECTATOR)
        game.set_seed(7)
        game.set_ticrate(35)
        game.set_episode_timeout(210)
        game.set_window_visible(True)
        game.set_sound_enabled(False)
        game.set_console_enabled(False)
        game.set_render_hud(True)
        game.set_render_all_frames(True)
        game.set_available_game_variables([vd.GameVariable.KILLCOUNT,
             vd.GameVariable.DEATHCOUNT, vd.GameVariable.SELECTED_WEAPON_AMMO])
        init_begin = time.perf_counter_ns()
        game.init()
        result['init_bracket_ns'] = [init_begin, time.perf_counter_ns()]
        windows = []
        until = time.monotonic() + 2
        while time.monotonic() < until:
            windows = [w for w in root.query_tree().children
                       if w.get_attributes().map_state == X.IsViewable]
            if len(windows) == 1:
                break
            time.sleep(.02)
        if len(windows) != 1:
            raise RuntimeError('expected one private mapped game window')
        window = windows[0]
        window.set_input_focus(X.RevertToParent, X.CurrentTime)
        connection.sync()
        focus = connection.get_input_focus().focus.id
        result['window'] = {'id': window.id, 'wm_name': window.get_wm_name(),
                            'wm_class': window.get_wm_class(), 'focus': focus}
        if focus != window.id:
            raise RuntimeError('game focus not observed')
        keycode = connection.keysym_to_keycode(XK.string_to_keysym('space'))
        if not keycode:
            raise RuntimeError('Space key unavailable')

        def key_state(label):
            begin = time.perf_counter_ns()
            bitmap = list(connection.query_keymap())
            event = {'event': 'independent_X11_keymap', 'label': label,
                     'begin_ns': begin, 'end_ns': time.perf_counter_ns(),
                     'keycode': keycode, 'bitmap': bitmap,
                     'space_down': bool(bitmap[keycode // 8] & (1 << (keycode % 8)))}
            result['events'].append(event)
            return event

        def score(label):
            # Only the recorder reads this object; the literal action never does.
            begin = time.perf_counter_ns()
            before = game.get_episode_time()
            sample = {'label': label, 'begin_ns': begin, 'episode_tic': before,
                      'kills': int(game.get_game_variable(vd.GameVariable.KILLCOUNT)),
                      'deaths': int(game.get_game_variable(vd.GameVariable.DEATHCOUNT)),
                      'ammo': int(game.get_game_variable(vd.GameVariable.SELECTED_WEAPON_AMMO)),
                      'finished': game.is_episode_finished(),
                      'dead': game.is_player_dead()}
            sample.update(episode_tic_after=game.get_episode_time(),
                          end_ns=time.perf_counter_ns())
            result['privileged_samples'].append(sample)
            return sample

        ImageGrab.grab(xdisplay=name).save(out / 'before.png')
        initial_keys = key_state('before')
        if any(initial_keys['bitmap']):
            raise RuntimeError('private X11 starts with a pressed key')
        score('before')
        owner = InputOwner(name)
        lease = Lease(time.perf_counter_ns() + 5_000_000_000)
        lease.expected_focus = focus
        lease.intent_token = 'game-b64b-' + kind
        started = time.perf_counter_ns()
        if kind == 'attack':
            result['events'].append(owner.call('down', lease, 'space'))
            key_state('held')
        # Independent real-time progression; no make_action/set_action/advance_action.
        for index in range(5):
            due = started + (index + 1) * 200_000_000
            time.sleep(max(0, (due - time.perf_counter_ns()) / 1e9))
            score('interval-' + str(index))
        if kind == 'attack':
            result['events'].append(owner.call('up', lease, 'space'))
        result['events'].append(owner.call('input_state'))
        key_state('after-explicit-up')
        result['events'].append(owner.call('release', lease))
        score('after-release')
        ImageGrab.grab(xdisplay=name).save(out / 'after.png')
        result['owner_records'] = owner.records
        result['owner_thread_alive_before_close'] = owner._inner.thread.is_alive()
        result['method'] = 'construction completed; independent retained-data disposition pending'
    except Exception as exc:
        result['error'] = {'type': type(exc).__name__, 'message': str(exc),
                           'traceback': traceback.format_exc()}
        result['method'] = 'FIRST_CONSTRUCTION_FAILURE'
    finally:
        for label, obj in [('owner', owner), ('game', game), ('X11_client', connection)]:
            if obj is None:
                continue
            begin = time.perf_counter_ns()
            try:
                obj.close()
                entry = {'resource': label, 'closed': True}
                if label == 'owner':
                    entry['thread_alive_after_close'] = obj._inner.thread.is_alive()
                    result['owner_records_after_close'] = obj.records
            except Exception as exc:
                entry = {'resource': label, 'closed': False, 'error': repr(exc)}
            entry['bracket_ns'] = [begin, time.perf_counter_ns()]
            result['cleanup'].append(entry)
        if xproc is not None:
            xproc.terminate()
            try:
                xproc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                xproc.kill()
                xproc.wait(timeout=2)
            result['cleanup'].append({'resource': 'Xvfb', 'pid': xproc.pid,
                                      'returncode': xproc.returncode})
            xlog.close()
        result['utc_end'] = datetime.now(timezone.utc).isoformat()
        write(out / 'ROW.json', result)
    return result


def valid_control(row):
    if row.get('error') or any(x.get('closed') is False for x in row['cleanup']):
        return False
    samples = row['privileged_samples']
    keys = [x for x in row['events'] if x.get('event') == 'independent_X11_keymap']
    return (samples[-1]['episode_tic'] > samples[0]['episode_tic']
            and all(x['ammo'] == samples[0]['ammo'] and x['kills'] == 0
                    and not x['dead'] for x in samples)
            and samples[0]['ammo'] > 0
            and all(not any(x['bitmap']) for x in keys)
            and not any(x.get('event') == 'input_admission' for x in row['events']))


def main():
    runtime = {'image': IMAGE, 'version': vd.__version__,
               'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in Path(__file__).parent.glob('*.py')},
               'limits': {n: Path('/sys/fs/cgroup', n).read_text().strip()
                          for n in ['cpu.max', 'memory.max', 'pids.max']}}
    write(OUT / 'RUNTIME.json', runtime)
    control = cell('control')
    if not valid_control(control):
        write(OUT / 'STOP.json', {'reason': 'invalid first no-input control; attack not run'})
        raise SystemExit(2)
    attack = cell('attack')
    if attack.get('error'):
        raise SystemExit(3)


if __name__ == '__main__':
    main()
