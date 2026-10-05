"""Single-use native boundary experiment; no game/model or product mutation."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
import types

sys.path.insert(0, '/preparation')
sys.path.insert(0, '/source/research/live_control')
from build_owner import instrument
from lease import Lease
from Xlib import X, XK, display

raw = Path('/source/research/live_control/input_owner_v10.py').read_bytes()
measured = instrument(raw)
result = dict(scope='full-owner-private-X11-component-only', cells=[],
    source_commit='96d39ca3855351b2501aab1da919941011190ac3',
    original_sha256=hashlib.sha256(raw).hexdigest(),
    measured_sha256=hashlib.sha256(measured.encode()).hexdigest(),
    runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
server = None
d = None
try:
    log = Path('/out/XVFB.txt').open('x')
    server = subprocess.Popen(['Xvfb', ':91', '-screen', '0', '640x480x24',
        '-nolisten', 'tcp'], stdout=log, stderr=subprocess.STDOUT)
    until = time.monotonic() + 3
    while not Path('/tmp/.X11-unix/X91').exists():
        if server.poll() is not None or time.monotonic() >= until:
            raise RuntimeError('fresh Xvfb did not become ready')
        time.sleep(.01)
    d = display.Display(':91')
    d.change_keyboard_control(auto_repeat_mode=X.AutoRepeatModeOff)
    w = d.screen().root.create_window(0, 0, 200, 100, 0,
        d.screen().root_depth, event_mask=X.KeyPressMask | X.KeyReleaseMask)
    w.map()
    d.set_input_focus(w, X.RevertToParent, X.CurrentTime)
    d.sync()
    assert d.get_input_focus().focus.id == w.id
    codes = {key: d.keysym_to_keycode(XK.string_to_keysym(key)) for key in 'abc'}
    expected = [(X.KeyPress, codes['a']), (X.KeyRelease, codes['a']),
        (X.KeyPress, codes['b']), (X.KeyPress, codes['c']),
        (X.KeyRelease, codes['b']), (X.KeyRelease, codes['c'])]
    for index, arm in enumerate(('original', 'measured', 'measured', 'original')):
        module = types.ModuleType('boundary_owner_' + str(index))
        exec(compile(raw if arm == 'original' else measured,
            '<' + module.__name__ + '>', 'exec'), module.__dict__)
        owner = module.InputOwner(':91')
        cell = dict(index=index, arm=arm, calls=[], received=[], records=[])
        result['cells'].append(cell)
        lease = Lease(time.perf_counter_ns() + 5_000_000_000)
        lease.expected_focus = w.id
        lease.token = 'a01-cell-' + str(index)
        foreign = Lease(time.perf_counter_ns() + 5_000_000_000)
        foreign.expected_focus = w.id
        foreign.token = 'foreign-' + str(index)
        try:
            for operation, key in (('down', 'a'), ('up', 'a'),
                    ('down', 'b'), ('down', 'c')):
                started = time.perf_counter_ns()
                response = owner.call(operation, lease, key)
                cell['calls'].append(dict(operation=operation, key=key,
                    started_ns=started, completed_ns=time.perf_counter_ns(),
                    response=response))
                if operation == 'up':
                    assert response is None
            try:
                owner.call('up', foreign, 'b')
            except ValueError as error:
                cell['foreign_up'] = dict(type=type(error).__name__, error=str(error))
            else:
                raise AssertionError('foreign up was admitted')
            released = owner.call('release', lease)
            cell['release'] = released
            assert released['verified'] is True and released['keys_down'] == []
            d.sync()
            while d.pending_events():
                event = d.next_event()
                if event.type in (X.KeyPress, X.KeyRelease):
                    cell['received'].append(dict(type=event.type, code=event.detail,
                        receipt_ns=time.perf_counter_ns(), xserver_ms=event.time))
            assert [(e['type'], e['code']) for e in cell['received']] == expected
            bitmap = d.query_keymap()
            cell['physical_down'] = [code for code in codes.values()
                if bitmap[code // 8] & (1 << (code % 8))]
            assert cell['physical_down'] == []
            if arm == 'measured':
                rows = [r for r in owner.records if r['event'] in
                    ('owner_key_press', 'owner_explicit_key_up')]
                assert [(r['event'], r['keycode']) for r in rows] == [
                    ('owner_key_press', codes['a']), ('owner_explicit_key_up', codes['a']),
                    ('owner_key_press', codes['b']), ('owner_key_press', codes['c'])]
                cleanup = released['key_release_brackets']
                assert [r['keycode'] for r in cleanup] == [codes['b'], codes['c']]
                assert cleanup[0]['sync_completed_ns'] == cleanup[1]['sync_completed_ns']
                for row in rows + cleanup:
                    assert row['owner_id'] == owner.owner_id
                    assert row['intent'] == lease.token
                    assert row['grants_input_authority'] is False
                    assert type(row['request_started_ns']) is int
                    assert type(row['sync_completed_ns']) is int
                    assert row['request_started_ns'] <= row['sync_completed_ns']
        finally:
            owner.close()
            cell['records'] = owner.records
            cell['owner_stopped'] = owner.stopped.is_set()
            cell['owner_error'] = repr(owner.error) if owner.error else None
        assert cell['owner_stopped'] and cell['owner_error'] is None
    result['disposition'] = 'PASS_NATIVE_OWNER_COMPONENT'
except Exception as error:
    result.update(disposition='STOP_NATIVE_BOUNDARY', error_type=type(error).__name__,
        error=str(error), traceback=traceback.format_exc())
finally:
    if d is not None:
        d.close()
    if server is not None:
        server.terminate()
        try:
            server.wait(timeout=2)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=2)
        result['xvfb_exit'] = server.returncode
    with Path('/out/RESULT.json').open('x') as stream:
        json.dump(result, stream, indent=2)
print(json.dumps(dict(disposition=result['disposition'], cells=len(result['cells']),
    error=result.get('error'))))
sys.exit(0 if result['disposition'] == 'PASS_NATIVE_OWNER_COMPONENT' else 1)
