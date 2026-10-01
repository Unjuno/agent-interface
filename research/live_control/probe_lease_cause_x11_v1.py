"""Actual X11 key hold/focus transfer; scripted infrastructure test, not self-use."""
import contextlib
import io
import json
import threading
import time
from pathlib import Path
import session_v6
from input_owner_v10 import InputOwner
from executor_v4 import Executor
from report_pages_v2 import digest

HERE = Path(__file__).resolve().parent


def main():
    out = HERE / 'results/lease-cause-x11-01'
    out.mkdir(exist_ok=False)
    events, checks = [], {}
    session = owner = executor = None
    held, resume, done = threading.Event(), threading.Event(), threading.Event()
    result = {'sources': {p.name: digest(p.read_bytes()) for p in (Path(__file__), HERE / 'input_owner_v10.py', HERE / 'executor_v4.py', HERE / 'lease_cause_v1.py')},
              'scope': 'One scripted private X11 focus transfer and subsequent same-deadline intent. No full app task, model use, or speed qualification.'}
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            session = session_v6.suite.Session()
            session_v6.suite.prepare(session, 'xterm', 930302, '')
            owner = InputOwner(session.name)
        X, XK = session_v6.suite.base.X, session_v6.suite.base.XK
        original = session.d.get_input_focus().focus
        sink = session.d.screen().root.create_window(0, 0, 100, 80, 0,
                    session.d.screen().root_depth, override_redirect=True)
        sink.map()
        session.d.sync()
        code = session.d.keysym_to_keycode(XK.string_to_keysym('Control_L'))
        def key_down():
            return bool(session.d.query_keymap()[code // 8] & (1 << (code % 8)))
        class Backend:
            sequence = 1
            def validate(self, steps):
                assert steps in ([{'op': 'transfer'}], [{'op': 'normal'}])
            def execute(self, step, lease, identifier, index):
                lease.expected_focus = original.id
                owner.call('down', lease, 'Control_L')
                if step['op'] == 'transfer':
                    held.set()
                    if not resume.wait(2):
                        raise RuntimeError('focus controller did not resume')
                    # Even after focus returns, the old lease must remain revoked.
                    owner.call('down', lease, 'Control_L')
            def release_all(self):
                return owner.call('release', self.lease)
        def emit(event):
            events.append(event)
            if event['event'] == 'terminal':
                done.set()
        executor = Executor(Backend(), emit)
        deadline = time.perf_counter_ns() + 10_000_000_000
        executor.submit('focus-transfer', [{'op': 'transfer'}], 1, deadline)
        assert held.wait(2), 'key admission not observed'
        checks['physical_key_down_before_transfer'] = key_down()
        assert checks['physical_key_down_before_transfer']
        sink.set_input_focus(X.RevertToParent, X.CurrentTime)
        session.d.sync()
        stop = time.perf_counter() + 1
        while key_down() and time.perf_counter() < stop:
            time.sleep(.002)
        checks['physical_key_released_after_transfer'] = not key_down()
        assert checks['physical_key_released_after_transfer']
        original.set_input_focus(X.RevertToParent, X.CurrentTime)
        session.d.sync()
        resume.set()
        assert done.wait(2)
        with executor.lock:
            assert executor.active is None
        first = [e for e in events if e['event'] == 'terminal'][0]
        assert first['status'] == 'needs_decision'
        assert first['interruption']['record']['reason'] == 'focus_changed'
        assert first['interruption']['record']['verified'] and first['release']['verified']
        assert first['release']['reason'] == 'release'
        checks['cause_visible_before_shutdown'] = True
        done.clear()
        executor.submit('fresh-normal', [{'op': 'normal'}], 1, deadline)
        assert done.wait(2)
        second = [e for e in events if e['event'] == 'terminal'][1]
        assert second['status'] == 'completed' and second['interruption'] is None
        checks['same_deadline_new_intent_has_no_old_cause'] = True
        checks['physical_key_up_after_second_terminal'] = not key_down()
        assert checks['physical_key_up_after_second_terminal']
        result['success'] = True
    except Exception as exc:
        result.update(success=False, error=repr(exc))
    finally:
        resume.set()
        cleanup = {}
        for name, resource in [('executor', executor), ('owner', owner), ('session', session)]:
            if resource is not None:
                try:
                    resource.close()
                    cleanup[name] = 'close returned'
                except Exception as exc:
                    cleanup[name] = repr(exc)
                    result['success'] = False
        result.update(checks=checks, events=events, owner_records=owner.records if owner else [], cleanup=cleanup)
        (out / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    if not result['success']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
