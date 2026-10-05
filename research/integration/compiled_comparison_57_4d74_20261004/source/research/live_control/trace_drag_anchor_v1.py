"""Diagnostic phase captures during held drag; added observation overhead is explicit."""
import contextlib
import json
import shutil
import time
from pathlib import Path
import numpy as np
from cause_session_v1 import Backend as Previous, suite
from executor_v5 import Executor
from executor_v3 import Cancelled
from report_pages_v2 import digest
from score_drag_v1 import score

HERE = Path(__file__).resolve().parent


def main():
    root = HERE / 'results/drag-anchor-01'
    root.mkdir(exist_ok=False)
    paths = {'coarse': [618, 628, 638], 'fine_start': [618, 619, 628, 638]}
    names = ['trace_drag_anchor_v1.py', 'cause_session_v1.py', 'input_owner_v10.py',
             'executor_v5.py', 'lease_cause_v2.py', 'score_drag_v1.py']
    plan = {'paths': paths, 'seed': 214, 'hold_between_samples_ms': 150,
            'sources': {n: digest((HERE / n).read_bytes()) for n in names},
            'hypothesis': 'first qualifying motion establishes anchor; remaining motions cause displacement',
            'scope': 'two diagnostic scripted arms; captures perturb timing; not performance or complete app event instrumentation'}
    (root / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
    for name, xs in paths.items():
        out = root / name
        out.mkdir()
        events, phases = [], []
        session = backend = engine = output = None
        result = {'name': name}
        try:
            class Backend(Previous):
                def execute(self, step, lease, identifier, index):
                    if identifier != 'trace' or step['op'] != 'pointer_drag':
                        return super().execute(step, lease, identifier, index)
                    # Diagnostic equivalent of current pointer binding and calls.
                    lease.expected_focus = self.observed_focus
                    binding = self.observed_pointer
                    lease.expected_surface = binding['surface']
                    lease.expected_geometry = list(binding['geometry'])
                    def call(op, payload):
                        record = self.owner.call(op, lease, payload)
                        if record is not None:
                            self.emit(dict(record, id=identifier, step=index))
                    def sample(label):
                        if lease.wait(.15):
                            raise Cancelled()
                        state = self.owner.call('input_state')
                        self.snapshot(identifier, index)
                        frame = self.decoder.frame
                        array = np.frombuffer(frame.pixels, np.uint8).reshape(frame.height, frame.width, 3)
                        # Canvas-only red pixels exclude palette and status swatch.
                        crop = array[300:550, 530:775]
                        ys, xx = np.where((crop[:, :, 0] > 240) & (crop[:, :, 1] < 20) & (crop[:, :, 2] < 20))
                        box = [int(xx.min()) + 530, int(ys.min()) + 300, int(xx.max()) + 530, int(ys.max()) + 300] if len(xx) else None
                        phases.append({'phase': label, 'state': state, 'red_bbox': box,
                                       'observation': events[-1]})
                    points = step['points']
                    call('move', points[0])
                    try:
                        call('button_down', 1)
                        sample('pressed')
                        for i, point in enumerate(points[1:], 1):
                            call('move', point)
                            sample('motion-' + str(i))
                    finally:
                        call('button_up', 1)
                    sample('released')
            with (out / 'setup.txt').open('w') as diagnostics, contextlib.redirect_stdout(diagnostics):
                session = suite.Session()
                _, output, _ = suite.prepare(session, 'inkscape', 214, '')
                backend = Backend(session, out, events.append)
            backend.snapshot('initial', 0)
            engine = Executor(backend, events.append)
            def submit(identifier, steps):
                engine.submit(identifier, steps, backend.sequence, time.perf_counter_ns() + 10_000_000_000)
                stop = time.monotonic() + 12
                while not any(e['event'] == 'terminal' and e['id'] == identifier for e in events) and time.monotonic() < stop:
                    time.sleep(.002)
                terminal = next(e for e in events if e['event'] == 'terminal' and e['id'] == identifier)
                assert terminal['status'] == 'completed', terminal
                with engine.lock:
                    assert engine.active is None
            submit('select', [{'op': 'pointer_click', 'x': 618, 'y': 391, 'duration_ms': 80},
                              {'op': 'settle', 'quiet_ms': 80, 'timeout_ms': 500}])
            submit('trace', [{'op': 'pointer_drag', 'points': [{'x': x, 'y': 391} for x in xs], 'duration_ms': 600}])
            submit('save', [{'op': 'chord', 'modifier': 'Control_L', 'key': 's'},
                            {'op': 'settle', 'quiet_ms': 80, 'timeout_ms': 500}])
            shutil.copy2(output, out / 'shape.svg')
            result['task_score'] = score(out / 'shape.svg')
            result['execution_completed'] = True
        except Exception as exc:
            result.update(execution_completed=False, error=repr(exc))
        finally:
            cleanup = {}
            for label, resource in [('engine', engine), ('backend', backend), ('session', session)]:
                if resource is not None:
                    try:
                        resource.close()
                        cleanup[label] = 'close returned'
                    except Exception as exc:
                        cleanup[label] = repr(exc)
                        result['execution_completed'] = False
            result.update(events=events, phases=phases, cleanup=cleanup,
                          owner_records=backend.owner.records if backend else [])
            (out / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps({'name': name, 'completed': result['execution_completed'],
                          'score': result.get('task_score'), 'error': result.get('error'),
                          'phases': [{k: p[k] for k in ('phase', 'red_bbox')} for p in phases]}), flush=True)


if __name__ == '__main__':
    main()
