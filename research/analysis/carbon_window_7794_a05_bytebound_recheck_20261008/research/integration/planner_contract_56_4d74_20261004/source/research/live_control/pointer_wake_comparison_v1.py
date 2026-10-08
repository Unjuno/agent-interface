"""Finite scripted actual-X11 comparison; same backend, owner, task and injection."""
import contextlib
import json
import time
from pathlib import Path
from Xlib import X, display
from cause_session_v1 import Backend, suite
from executor_v4 import Executor as Old
from executor_v5 import Executor as New
from report_pages_v2 import digest

HERE = Path(__file__).resolve().parent


def main():
    root = HERE / 'results/pointer-wake-comparison-01'
    root.mkdir(exist_ok=False)
    allocations = [('click', True, ['old', 'new'], 211),
                   ('drag', True, ['new', 'old'], 212),
                   ('drag', False, ['old', 'new'], 213)]
    names = ['pointer_wake_comparison_v1.py', 'cause_session_v1.py', 'input_owner_v10.py',
             'executor_v4.py', 'executor_v5.py', 'executor_v3.py', 'lease_cause_v1.py',
             'lease_cause_v2.py', 'lease.py', 'session_v8.py', 'session_v7.py',
             'session_v6.py', 'session_v5.py', 'session_v4.py', 'quiet_window.py']
    plan = {'allocations': allocations, 'sources': {n: digest((HERE / n).read_bytes()) for n in names},
            'scope': 'six scripted actual app arms; not model performance, no reruns, retained failures',
            'deadline_ms': 5000, 'injection': 'transfer focus after physical Button1 down, restore after release',
            'steps': {'click': [{'op': 'pointer_click', 'x': 618, 'y': 391, 'duration_ms': 250}],
                      'drag': [{'op': 'pointer_drag', 'points': [{'x': 618, 'y': 391}, {'x': 638, 'y': 391}], 'duration_ms': 1000}]}}
    (root / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
    results = []
    for index, (kind, interrupt, order, seed) in enumerate(allocations):
        for candidate in order:
            out = root / f'{index}-{candidate}'
            out.mkdir()
            events, result = [], {'kind': kind, 'interrupt': interrupt, 'candidate': candidate, 'seed': seed}
            session = backend = engine = controller = sink = original = None
            try:
                with (out / 'setup.txt').open('w') as diagnostics, contextlib.redirect_stdout(diagnostics):
                    session = suite.Session()
                    suite.prepare(session, 'inkscape', seed, '')
                    backend = Backend(session, out, events.append)
                    controller = display.Display(session.name)
                backend.snapshot('initial', 0)
                result['initial_png_sha256'] = digest(Path(events[-1]['image']).read_bytes())
                engine = (Old if candidate == 'old' else New)(backend, events.append)
                def down():
                    return bool(controller.screen().root.query_pointer().mask & X.Button1Mask)
                engine.submit('one', plan['steps'][kind], backend.sequence, time.perf_counter_ns() + 5_000_000_000)
                stop = time.monotonic() + 2
                while not down() and time.monotonic() < stop:
                    time.sleep(.002)
                assert down(), 'physical button admission not observed'
                result['physical_down_observed'] = True
                if interrupt:
                    original = controller.get_input_focus().focus
                    sink = controller.screen().root.create_window(0, 0, 100, 80, 0,
                            controller.screen().root_depth, override_redirect=True)
                    sink.map()
                    sink.set_input_focus(X.RevertToParent, X.CurrentTime)
                    controller.sync()
                    result['transfer_ns'] = time.perf_counter_ns()
                    stop = time.monotonic() + 1
                    while down() and time.monotonic() < stop:
                        time.sleep(.002)
                    result['physical_up_after_transfer'] = not down()
                    assert not down(), 'button not released'
                    original.set_input_focus(X.RevertToParent, X.CurrentTime)
                    controller.sync()
                stop = time.monotonic() + 3
                while not any(e['event'] == 'terminal' for e in events) and time.monotonic() < stop:
                    time.sleep(.002)
                terminals = [e for e in events if e['event'] == 'terminal']
                assert len(terminals) == 1
                terminal = terminals[0]
                result['terminal'] = terminal
                result['physical_up_after_terminal'] = not down()
                assert not down() and terminal['release']['verified']
                moves = [e for e in events if e['event'] == 'pointer_admission' and e['operation'] == 'move']
                result['admitted_moves'] = [e['payload'] for e in moves]
                if interrupt:
                    cause = terminal['interruption']['record']
                    assert cause['reason'] == 'focus_changed' and cause['verified']
                    assert len(moves) == 1, 'drag tail admitted after interruption'
                    result['release_to_terminal_ms'] = (terminal['terminal_ns'] - cause['verified_ns']) / 1e6
                    expected = 'completed' if candidate == 'old' and kind == 'click' else 'needs_decision'
                    assert terminal['status'] == expected
                    if candidate == 'new':
                        assert terminal['steps_completed'] == 0
                else:
                    assert terminal['status'] == 'completed' and terminal['interruption'] is None
                    assert result['admitted_moves'] == plan['steps']['drag'][0]['points']
                result['checks_passed'] = True
            except Exception as exc:
                result.update(checks_passed=False, error=repr(exc))
            finally:
                cleanup = {}
                if original is not None:
                    original.set_input_focus(X.RevertToParent, X.CurrentTime)
                    controller.sync()
                if sink is not None:
                    sink.destroy()
                    controller.sync()
                for name, resource in [('engine', engine), ('backend', backend), ('controller', controller), ('session', session)]:
                    if resource is not None:
                        try:
                            resource.close()
                            cleanup[name] = 'close returned'
                        except Exception as exc:
                            cleanup[name] = repr(exc)
                            result['checks_passed'] = False
                result.update(events=events, owner_records=backend.owner.records if backend else [], cleanup=cleanup)
                (out / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
            results.append(result)
            print(json.dumps({k: result.get(k) for k in ['kind', 'interrupt', 'candidate', 'checks_passed', 'error', 'release_to_terminal_ms']}), flush=True)
    pairs = []
    for i in range(0, len(results), 2):
        a, b = results[i:i+2]
        pairs.append({'kind': a['kind'], 'interrupt': a['interrupt'],
                      'same_initial_pixels': a.get('initial_png_sha256') == b.get('initial_png_sha256')})
    summary = {'success': all(r['checks_passed'] for r in results) and all(p['same_initial_pixels'] for p in pairs),
               'pairs': pairs, 'scope': plan['scope']}
    (root / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary))
    if not summary['success']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
