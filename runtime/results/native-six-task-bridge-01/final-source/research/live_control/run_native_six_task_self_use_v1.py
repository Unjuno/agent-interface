"""Primary-assistant six-task use of the existing native handle bridge.

Navigation uses the existing research keyboard driver (native text cannot type
URLs). Guarded field/Save interactions use NativeHandleBridge. No helper model.
"""
import argparse
import json
from pathlib import Path
import shutil
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "observation_gating"))
import gui_suite as suite
from integrated_efficiency_fixture_v1 import Fixture
import integrated_efficiency_runtime_v1 as integrated
from native_handle_bridge_v1 import NativeHandleBridge


class PrivateSession(suite.Session):
    def _popen(self, args, **kwargs):
        if Path(args[0]).name == "Xvfb":
            args = [*args, "-nolisten", "unix"]
        return super()._popen(args, **kwargs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=991083)
    parser.add_argument("--chromium", default="/home/taka/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome")
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    session = bridge = fixture = None
    rows = []

    def save(name, value):
        (out/name).write_text(json.dumps(value, indent=2)+'\n')

    def request_grounding(name, source):
        request = out/(name+'-grounding.json')
        save(name+'-source.json', source)
        print(json.dumps({'needs_grounding': name, 'source_sequence': source['sequence'],
                          'image': source['native']['artifact']['path'], 'request_file': str(request)}), flush=True)
        end = time.monotonic()+300
        while not request.exists():
            if time.monotonic()>end:
                raise RuntimeError('primary-assistant grounding timeout')
            time.sleep(.05)
        grounding = json.loads(request.read_text())
        if grounding['source_sequence'] != source['sequence']:
            raise ValueError('grounding source does not match presented source')
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
        driver = suite.base.Driver(session)

        def navigate(task):
            started = time.monotonic_ns()
            before = driver.input_events
            driver.chord('Control_L', 'l')
            driver.text(task['url'])
            driver.key('Return')
            session.wait_window('AI INTEGRATED '+task['task_id']+' READY', 10)
            # Bounded rendering allowance; readiness title is not a task score.
            time.sleep(.2)
            return {'elapsed_ms': (time.monotonic_ns()-started)/1e6,
                    'input_events': driver.input_events-before, 'path': 'existing research Driver'}

        navigation = navigate(goal['tasks'][0])
        window = next(line.split()[0] for line in session.windows().splitlines()
                      if 'AI INTEGRATED task-1 READY' in line)
        bridge = NativeHandleBridge(session.name, {'browser': int(window, 16)}, 'browser', out/'bridge')
        source = bridge.observe()
        handles = request_grounding('cold', source)
        repaired = False
        for index, task in enumerate(goal['tasks']):
            if index:
                navigation = navigate(task)
            before = bridge.backend.emissions
            started = time.monotonic_ns()
            entered = bridge.click(*handles['field'], tail=[
                {'op': 'key_chord', 'keys': ['CTRL', 'A']},
                {'op': 'text', 'text': task['token']},
                {'op': 'wait_update', 'timeout_ms': 100}])
            row = {'task_id': task['task_id'], 'navigation': navigation, 'entered': entered}
            rows.append(row)
            save('tasks.json', rows)
            if entered['status'] != 'completed':
                row['refusal_emissions'] = bridge.backend.emissions-before
                save('tasks.json', rows)
                if entered['status'] != 'refused' or repaired:
                    raise RuntimeError('unplanned partial or repeated refusal; inspect, no replay')
                # One explicit assistant repair from a newly viewed source.
                source = bridge.observe()
                handles = request_grounding('repair', source)
                repaired = True
                entered = bridge.click(*handles['field'], tail=[
                    {'op': 'key_chord', 'keys': ['CTRL', 'A']},
                    {'op': 'text', 'text': task['token']},
                    {'op': 'wait_update', 'timeout_ms': 100}])
                row['repaired_enter'] = entered
                save('tasks.json', rows)
                if entered['status'] != 'completed':
                    raise RuntimeError('repair did not complete; no further input')
            saved = bridge.click(*handles['submit'], tail=[{'op': 'wait_update', 'timeout_ms': 100}])
            row['saved'] = saved
            row['local_elapsed_ms'] = (time.monotonic_ns()-started)/1e6
            save('tasks.json', rows)
            if saved['status'] != 'completed':
                raise RuntimeError('Save did not complete; retain entered effect, no replay')
            session.wait_window('AI INTEGRATED SAVED', 10)
        final = bridge.observe()
        save('final-source.json', final)
        save('evaluation.json', fixture.evaluate())
        print(json.dumps({'evaluation': fixture.evaluate(), 'final_image': final['native']['artifact']['path']}), flush=True)
    except Exception:
        (out/'error.txt').write_text(traceback.format_exc())
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
