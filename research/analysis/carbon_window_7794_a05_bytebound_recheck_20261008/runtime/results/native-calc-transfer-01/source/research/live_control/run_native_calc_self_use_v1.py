"""Primary-assistant Calc transfer using existing setup, bridge and scorer."""
import argparse
import json
from pathlib import Path
import shutil
import time
import traceback

from run_native_six_task_self_use_v1 import PrivateSession, suite
from native_handle_bridge_v1 import NativeHandleBridge


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seed', type=int, default=991084)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    session = bridge = output = None
    goal = None
    rows = []

    def save(name, value):
        (out/name).write_text(json.dumps(value, indent=2)+'\n')

    try:
        session = PrivateSession()
        goal, output, _ = suite.prepare(session, 'calc', args.seed, '')
        save('goal.json', goal)
        window = int(next(line.split()[0] for line in session.windows().splitlines()
                          if 'sheet.xlsx' in line), 16)
        for stage in range(1, 5):
            bridge = NativeHandleBridge(session.name, {'app': window}, 'app', out/f'bridge-{stage}')
            source = bridge.observe()
            windows = session.windows()
            save(f'source-{stage}.json', source)
            save(f'windows-{stage}.json', windows)
            request = out/f'request-{stage}.json'
            print(json.dumps({'stage': stage, 'goal': goal,
                'source_sequence': source['sequence'], 'image': source['native']['artifact']['path'],
                'windows': windows, 'request_file': str(request)}), flush=True)
            deadline = time.monotonic()+300
            while not request.exists():
                if time.monotonic() > deadline:
                    raise TimeoutError('primary-assistant decision timeout')
                time.sleep(.05)
            decision = json.loads(request.read_text())
            if decision['source_sequence'] != source['sequence']:
                raise ValueError('decision must refer to exact presented source')
            if decision.get('finish') is True:
                break
            started = time.monotonic_ns()
            offset = bridge.mint('target', source['sequence'], decision['point'], region_size=(24, 14))
            result = bridge.click('target', offset, tail=decision.get('tail', []))
            row = {'stage': stage, 'result': result, 'started_ns': started}
            rows.append(row)
            save('actions.json', rows)
            if result['status'] != 'completed':
                raise RuntimeError('native action '+result['status']+'; no replay')
            # Same feedback contract as Chromium. Focus changes return a fresh
            # image needing review, not a guessed dialog confirmation.
            row['feedback'] = bridge.feedback(decision['expected_title'], timeout_ms=2000)
            row['ended_ns'] = time.monotonic_ns()
            save('actions.json', rows)
            print(json.dumps({'stage': stage, 'feedback': row['feedback']}), flush=True)
            focus = bridge.backend.d.get_input_focus().focus
            window = getattr(focus, 'id', None)
            if not window:
                raise RuntimeError('no focused window for explicit next-stage review')
            bridge.close()
            bridge = None
        else:
            raise RuntimeError('bounded action stages exhausted without explicit finish')
        save('evaluation.json', suite.evaluate('calc', output, goal))
        print(json.dumps({'evaluation': json.loads((out/'evaluation.json').read_text())}), flush=True)
    except Exception:
        (out/'error.txt').write_text(traceback.format_exc())
        raise
    finally:
        if output is not None and output.exists():
            shutil.copyfile(output, out/'sheet.xlsx')
        if bridge is not None:
            bridge.close()
        if session is not None:
            session.close()
            save('cleanup.json', [{'pid': p.pid, 'returncode': p.poll()} for p in session.procs])


if __name__ == '__main__':
    main()
