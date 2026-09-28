"""Primary-assistant six-task use of the existing native handle bridge.

Navigation uses the public native dispatch API. Guarded field/Save interactions
use NativeHandleBridge. No helper model.
"""
import argparse
import json
from pathlib import Path
import shutil
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
# Direct script execution needs both local research modules and the runtime package.
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent / "observation_gating"))
# Select one exact built runtime before importing any runtime-backed wrappers.
# The fixture and primary-review exchange stay in the research harness.
_archive_parser = argparse.ArgumentParser(add_help=False)
_archive_parser.add_argument('--runtime-archive', type=Path)
_archive_args, _ = _archive_parser.parse_known_args()
if _archive_args.runtime_archive:
    _runtime_archive = _archive_args.runtime_archive.resolve(strict=True)
    sys.path.insert(0, str(_runtime_archive))

import gui_suite as suite
from integrated_efficiency_fixture_v1 import Fixture
import integrated_efficiency_runtime_v1 as integrated
from runtime.guarded_x11_v1.bridge import NativeHandleBridge, read_window_title
from runtime.cli_v1.api import dispatch
from runtime.core_v1.contract import SCHEMA_PROGRAM


class PrivateSession(suite.Session):
    def windows(self):
        lines = []
        for line in super().windows().splitlines():
            fields = line.split(None, 3)
            if len(fields) == 4 and fields[3] == 'N/A':
                try:
                    window = self.d.create_resource_object('window', int(fields[0], 16))
                    title = read_window_title(self.d, window)
                    if title:
                        fields[3] = title.replace('\n', ' ').replace('\r', ' ')
                        line = ' '.join(fields)
                except Exception:
                    # Disappearing/unreadable clients remain unrecognized.
                    pass
            lines.append(line)
        return '\n'.join(lines) + ('\n' if lines else '')

    def _popen(self, args, **kwargs):
        if Path(args[0]).name == "Xvfb":
            args = [*args, "-nolisten", "unix"]
        return super()._popen(args, **kwargs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-archive", type=Path, help="explicit built runtime used for all runtime imports")
    parser.add_argument("--route", choices=["persistent", "direct"], default="persistent")
    parser.add_argument('--primary-review', action='store_true',
                        help='require primary image/receipt review before advancing each task')
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=991083)
    parser.add_argument("--negative-task", choices=[f'task-{i}' for i in range(1, 7)],
                        help="Controlled fixture-only wrong-value input; expect stop on rejection")
    parser.add_argument("--chromium", default="/home/taka/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome")
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    session = bridge = fixture = None
    rows = []

    def save(name, value):
        (out/name).write_text(json.dumps(value, indent=2)+'\n')

    def request_grounding(name, source, *, prior_receipt=None):
        from native_primary_review_v1 import grounding_notice
        grounding_started = time.monotonic_ns()
        request = out/(name+'-grounding.json')
        save(name+'-source.json', source)
        print(json.dumps(grounding_notice(name, source, request,
                         prior_receipt=prior_receipt, receipt_file=out/'tasks.json')), flush=True)
        end = time.monotonic()+300
        while not request.exists():
            if time.monotonic()>end:
                raise RuntimeError('primary-assistant grounding timeout')
            time.sleep(.05)
        grounding = json.loads(request.read_text())
        if grounding['source_sequence'] != source['sequence']:
            raise ValueError('grounding source does not match presented source')
        save(name+'-grounding-timing.json', {'requested_ns': grounding_started, 'received_ns': time.monotonic_ns()})
        if args.route == 'direct':
            from native_direct_task_v1 import validate_grounding
            validate_grounding(source, grounding)
            return grounding
        for kind in ('field', 'submit'):
            offset = bridge.mint(name+'_'+kind, source['sequence'], grounding[kind+'_point'],
                                 region_size=(24, 38) if kind=='field' else (24, 14))
        return {kind: (name+'_'+kind, [12, 19] if kind=='field' else [12, 7])
                for kind in ('field', 'submit')}

    try:
        session = PrivateSession()
        goal, history, server = integrated.prepare(session, 'chromium', args.seed, args.chromium)
        fixture = integrated._ACTIVE[str(history)]
        save('goal.json', goal)
        import runtime.guarded_x11_v1.bridge as loaded_bridge
        import runtime.cli_v1.api as loaded_api
        save('runtime-origin.json', {'bridge': loaded_bridge.__file__, 'api': loaded_api.__file__,
             'archive': str(args.runtime_archive.resolve()) if args.runtime_archive else None})
        save('allocation.json', {'negative_task': args.negative_task, 'route': args.route,
                                 'primary_review': args.primary_review})
        window = next(line.split()[0] for line in session.windows().splitlines()
                      if 'about:blank' in line)
        targets = {'browser': int(window, 16)}
        bridge = NativeHandleBridge(session.name, targets, 'browser', out/'bridge')

        def review(row):
            if args.primary_review:
                from native_primary_review_v1 import review_task
                source = bridge.observe()
                row['primary_review'] = review_task(out, row['task_id'], source, row)
                save('tasks.json', rows)

        def navigate(task):
            started = time.monotonic_ns()
            source = bridge.observe()
            program = {
                'schema': SCHEMA_PROGRAM, 'program_id': 'navigate-'+task['task_id'],
                'source': {'observation_seq': source['sequence'], 'binding_revision': 0},
                'authority': {'lease_id': 'native-navigation',
                              'expires_at_ns': time.monotonic_ns()+5_000_000_000},
                'terminal': {'release_all_required': True},
                'ops': [{'op': 'focus', 'target': 'browser'},
                        {'op': 'key_chord', 'keys': ['CTRL', 'l']},
                        {'op': 'wait_update', 'timeout_ms': 100},
                        {'op': 'text', 'text': task['url']},
                        {'op': 'wait_update', 'timeout_ms': 100},
                        {'op': 'key_chord', 'keys': ['ENTER']},
                        {'op': 'release_all'}]}
            save(task['task_id']+'-navigation-program.json', program)
            result = dispatch(program, targets, current_observation_seq=source['sequence'],
                              current_binding_revision=0, display_name=session.name)
            save(task['task_id']+'-navigation-result.json', result)
            if result.get('status') != 'returned' or result.get('result', {}).get('status') != 'completed':
                raise RuntimeError('native navigation did not complete; no replay')
            session.wait_window('AI INTEGRATED '+task['task_id']+' READY', 10)
            # Bounded rendering allowance; readiness title is not a task score.
            time.sleep(.2)
            return {'elapsed_ms': (time.monotonic_ns()-started)/1e6,
                    'input_events': result['result']['execution']['program_emissions'],
                    'path': 'runtime.cli_v1.api.dispatch', 'result': result}

        navigation = navigate(goal['tasks'][0])
        source = bridge.observe()
        handles = request_grounding('cold', source)
        repaired = False
        for index, task in enumerate(goal['tasks']):
            if index:
                navigation = navigate(task)
            if args.route == 'direct':
                from native_direct_task_v1 import build_program
                if index:
                    source = bridge.observe()
                    handles = request_grounding(task['task_id'], source)
                token = task['token'] + ('-wrong' if task['task_id'] == args.negative_task else '')
                program = build_program(source, handles, token, task['task_id'], time.monotonic_ns())
                save(task['task_id']+'-direct-program.json', program)
                started = time.monotonic_ns()
                result = dispatch(program, targets, current_observation_seq=source['sequence'],
                                  current_binding_revision=source['binding_revision'], display_name=session.name)
                row = {'task_id': task['task_id'], 'navigation': navigation, 'direct': result,
                       'action_started_ns': started,
                       'dispatch_ms': (time.monotonic_ns()-started)/1e6}
                rows.append(row)
                save('tasks.json', rows)
                if result.get('status') != 'returned' or result.get('result', {}).get('status') != 'completed':
                    raise RuntimeError('direct task did not complete; no replay')
                feedback = bridge.feedback('AI INTEGRATED SAVED - Google Chrome for Testing',
                                          rejected_titles=['AI INTEGRATED REJECTED - Google Chrome for Testing'])
                row['feedback'] = feedback
                row['feedback_received_ns'] = time.monotonic_ns()
                row['through_feedback_ms'] = (time.monotonic_ns()-started)/1e6
                save('tasks.json', rows)
                if feedback['status'] != 'matched':
                    raise RuntimeError('direct task feedback '+feedback['status']+'; no replay')
                review(row)
                continue
            from runtime.guarded_x11_v1.form import fill_and_submit
            before = bridge.backend.emissions
            started = time.monotonic_ns()
            token = task['token'] + ('-wrong' if task['task_id'] == args.negative_task else '')
            row = {'task_id': task['task_id'], 'navigation': navigation,
                   'action_started_ns': started}
            rows.append(row)

            def retain_step(name, result, *, repair=False):
                row['repaired_enter' if repair and name == 'entered' else name] = result
                save('tasks.json', rows)

            method = fill_and_submit(bridge, handles, token, wait_ms=100, on_step=retain_step)
            row['method'] = {k: v for k, v in method.items() if k != 'results'}
            save('tasks.json', rows)
            if method['status'] != 'completed':
                row['refusal_emissions'] = bridge.backend.emissions-before
                save('tasks.json', rows)
                entered = row.get('entered', {})
                if (method['stopped_at'] != 'entered' or entered.get('status') != 'refused'
                        or row['refusal_emissions'] != 0 or repaired):
                    raise RuntimeError('unplanned partial or repeated refusal; inspect, no replay')
                # One explicit assistant repair, only after zero-emission refusal.
                source = bridge.observe()
                handles = request_grounding('repair', source, prior_receipt=row)
                repaired = True
                method = fill_and_submit(bridge, handles, token, wait_ms=100,
                    on_step=lambda name, result: retain_step(name, result, repair=True))
                row['repaired_method'] = {k: v for k, v in method.items() if k != 'results'}
                save('tasks.json', rows)
                if method['status'] != 'completed':
                    raise RuntimeError('repair did not complete; no further input')
            row['local_elapsed_ms'] = (time.monotonic_ns()-started)/1e6
            save('tasks.json', rows)
            feedback = bridge.feedback('AI INTEGRATED SAVED - Google Chrome for Testing',
                                      rejected_titles=['AI INTEGRATED REJECTED - Google Chrome for Testing'])
            row['feedback'] = feedback
            row['feedback_received_ns'] = time.monotonic_ns()
            row['through_feedback_ms'] = (time.monotonic_ns()-started)/1e6
            save('tasks.json', rows)
            if feedback['status'] != 'matched':
                raise RuntimeError('application feedback '+feedback['status']+'; no next task or input replay')
            review(row)
        final = bridge.observe()
        save('final-source.json', final)
        save('evaluation.json', fixture.evaluate())
        print(json.dumps({'evaluation': fixture.evaluate(), 'final_image': final['native']['artifact']['path']}), flush=True)
    except Exception:
        (out/'error.txt').write_text(traceback.format_exc())
        if bridge is not None:
            try:
                save('error-source.json', bridge.observe())
                save('error-windows.json', session.windows())
            except Exception:
                (out/'error-observation.txt').write_text(traceback.format_exc())
        raise
    finally:
        if fixture is not None:
            save('evaluation-at-close.json', fixture.evaluate())
            if fixture.history.exists():
                shutil.copyfile(fixture.history, out/'submission-history.jsonl')
            fixture.close()
        if bridge is not None:
            bridge.close()
        if session is not None:
            session.close()
            save('cleanup.json', [{'pid':p.pid,'returncode':p.poll()} for p in session.procs])


if __name__ == '__main__':
    main()
