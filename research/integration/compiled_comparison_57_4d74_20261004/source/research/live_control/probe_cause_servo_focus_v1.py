"""Actual servo yield interrupted by private focus transfer during blocked output."""
import contextlib
import json
import threading
import time
from pathlib import Path
from Xlib import X, display
from cause_servo_session_v1 import Backend, suite
from executor_v5 import Executor
from report_pages_v2 import digest

HERE = Path(__file__).resolve().parent


def main():
    out = HERE / 'results/cause-servo-focus-01'
    out.mkdir(exist_ok=False)
    blocked, resume, done = threading.Event(), threading.Event(), threading.Event()
    events = []
    result = {'scope': 'one scripted focus fault at servo yield; blocked output, not model latency',
              'sources': {n: digest((HERE / n).read_bytes()) for n in ['probe_cause_servo_focus_v1.py',
               'cause_servo_session_v1.py', 'cause_session_v1.py', 'session_v21.py', 'session_v15.py',
               'input_owner_v10.py', 'executor_v5.py', 'lease_cause_v2.py', 'patch_servo_v5.py']}}
    session = backend = engine = controller = original = sink = None
    try:
        def emit(e):
            events.append(e)
            if e['event'] == 'pointer_yield':
                blocked.set()
                assert resume.wait(2), 'controller did not resume output'
            if e['event'] == 'terminal':
                done.set()
        with (out / 'setup.txt').open('w') as diagnostics, contextlib.redirect_stdout(diagnostics):
            session = suite.Session()
            suite.prepare(session, 'inkscape', 216, '')
            backend = Backend(session, out, emit)
            controller = display.Display(session.name)
        backend.snapshot('initial', 0)
        engine = Executor(backend, emit)
        engine.submit('fault', [{'op': 'pointer_servo', 'source_sequence': backend.sequence,
                      'box': [592, 369, 56, 44], 'target_delta': [20, 0],
                      'points': [{'x': 618, 'y': 391}, {'x': 628, 'y': 391}],
                      'duration_ms': 100, 'max_corrections': 3}], backend.sequence,
                      time.perf_counter_ns() + 10_000_000_000)
        assert blocked.wait(3), 'servo yield not reached'
        def down():
            return bool(controller.screen().root.query_pointer().mask & X.Button1Mask)
        assert down()
        result['physical_button_down_at_yield'] = True
        original = controller.get_input_focus().focus
        sink = controller.screen().root.create_window(0, 0, 100, 80, 0,
                controller.screen().root_depth, override_redirect=True)
        sink.map()
        sink.set_input_focus(X.RevertToParent, X.CurrentTime)
        controller.sync()
        stop = time.monotonic() + 1
        while down() and time.monotonic() < stop:
            time.sleep(.002)
        result['physical_release_while_output_blocked'] = not down() and not resume.is_set() and not done.is_set()
        assert result['physical_release_while_output_blocked']
        original.set_input_focus(X.RevertToParent, X.CurrentTime)
        controller.sync()
        resume.set()
        assert done.wait(2)
        terminal = next(e for e in events if e['event'] == 'terminal')
        assert terminal['status'] == 'needs_decision' and terminal['steps_completed'] == 0
        assert terminal['decision_reason'] == 'focus_changed'
        assert terminal['interruption']['record']['reason'] == 'focus_changed'
        assert terminal['release']['verified']
        assert not any(e['event'] == 'servo_feedback' for e in events)
        assert not any(e.get('continuation') for e in events)
        result['no_post_release_policy_or_correction'] = True
        with engine.lock:
            assert engine.active is None
        done.clear()
        engine.submit('fresh-observation', [{'op': 'observe'}], backend.sequence,
                      time.perf_counter_ns() + 5_000_000_000)
        assert done.wait(2)
        final = [e for e in events if e['event'] == 'terminal'][-1]
        assert final['status'] == 'completed' and final['interruption'] is None
        result['success'] = True
    except Exception as exc:
        result.update(success=False, error=repr(exc))
    finally:
        resume.set()
        if original is not None:
            original.set_input_focus(X.RevertToParent, X.CurrentTime)
            controller.sync()
        if sink is not None:
            sink.destroy()
            controller.sync()
        cleanup = {}
        for name, resource in [('engine', engine), ('backend', backend), ('controller', controller), ('session', session)]:
            if resource is not None:
                try:
                    resource.close()
                    cleanup[name] = 'close returned'
                except Exception as exc:
                    cleanup[name] = repr(exc)
                    result['success'] = False
        result.update(events=events, cleanup=cleanup, owner_records=backend.owner.records if backend else [])
        (out / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result.get(k) for k in ['success', 'error', 'physical_release_while_output_blocked', 'no_post_release_policy_or_correction']}))
    if not result['success']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
