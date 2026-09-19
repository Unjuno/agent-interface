"""Primary-assistant desktop transfer; Calc remains the default workload."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import traceback

from run_native_six_task_self_use_v1 import PrivateSession, suite
from native_handle_bridge_v1 import NativeHandleBridge
from native_exchange_v1 import publish, encoded, current_owner_identity
from native_visual_watch_v1 import NativeVisualWatch
from native_release_observation_v1 import observe_release_failure
from native_cleanup_v1 import finish_allocation


def paced_text_tail(ops, gap_ms):
    """Explicit research policy compiled to ordinary native text/wait ops."""
    if type(gap_ms) is not int or gap_ms not in (0, 2, 10):
        raise ValueError('supported text gaps are 0, 2, 10 ms')
    if gap_ms == 0:
        return list(ops)
    result = []
    for op in ops:
        if op.get('op') != 'text' or not op.get('text'):
            result.append(op)
            continue
        for i, ch in enumerate(op['text']):
            if i:
                result.append({'op': 'wait_update', 'timeout_ms': gap_ms})
            result.append(dict(op, text=ch))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--app', choices=('calc', 'inkscape', 'calc-inkscape'), default='calc')
    parser.add_argument('--max-stages', type=int, choices=range(2,65), default=4)
    parser.add_argument('--seed', type=int, default=991084)
    parser.add_argument('--text-gap-ms', type=int, choices=(0, 2, 10), default=0)
    parser.add_argument('--probe-old-target', action='store_true')
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    publish(out/'owner.json', encoded(current_owner_identity()))
    publish(out/'exchange-contract.json', encoded({
        'schema': 'agent-interface/native-exchange-contract-v1', 'max_stages': args.max_stages}))
    session = bridge = output = None
    goal = None
    rows = []
    workloads = {}
    retired_targets = []
    stage = decision_hash = None
    terminal_reply = None

    def save(name, value):
        (out/name).write_text(json.dumps(value, indent=2)+'\n')

    try:
        session = PrivateSession()
        apps = ('calc', 'inkscape') if args.app == 'calc-inkscape' else (args.app,)
        for index, app in enumerate(apps):
            app_goal, output, _ = suite.prepare(session, app, args.seed + index, '')
            if app == 'calc':
                # Public task destination, not an inferred controller convention.
                app_goal['task'] = {'kind': 'write_cells',
                    'cells': {'A1': app_goal['a'], 'A2': app_goal['b']},
                    'save_format': 'xlsx'}
            elif app == 'inkscape':
                # This fixture scores direction/shape preservation, not exact
                # keyboard gain. Its dx is a nominal screen-space drag offset.
                app_goal['task'] = {'kind': 'move_right_preserve_geometry',
                    'x_greater_than': 50.5, 'y': 50, 'width': 40, 'height': 30,
                    'geometry_tolerance_exclusive': 0.1, 'transform': None,
                    'coordinate_frame': 'svg_user_units', 'save_format': 'svg',
                    'dx_meaning': 'nominal_drag_screen_px_not_exact_keyboard_displacement'}
            workloads[app] = {'goal': app_goal, 'output': output}
        goal = ({app: data['goal'] for app, data in workloads.items()}
                if len(workloads) > 1 else app_goal)
        save('goal.json', goal)
        save('workload.json', {'app': args.app, 'seed': args.seed,
            'preparation_order': list(apps), 'max_stages': args.max_stages})
        save('text-policy.json', {'gap_ms': args.text_gap_ms, 'default_changed': False})
        window = int(next(line.split()[0] for line in session.windows().splitlines()
                          if output.name in line), 16)
        bridge = NativeHandleBridge(session.name, {'app': window}, 'app', out/'bridge')
        source = bridge.observe()
        for stage in range(1, args.max_stages + 1):
            windows = session.windows()
            decision_hash = None
            if not (out/f'source-{stage}.json').exists():
                publish(out/f'source-{stage}.json', encoded(source))
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
            request_bytes = request.read_bytes()
            decision_hash = hashlib.sha256(request_bytes).hexdigest()
            decision = json.loads(request_bytes)
            if decision['source_sequence'] != source['sequence']:
                raise ValueError('decision must refer to exact presented source')
            if decision.get('finish') is True:
                break
            interaction = decision.get('interaction', 'click')
            if interaction not in ('click', 'keyboard'):
                raise ValueError('interaction must be click or keyboard')
            # Validate caller-placed lanes against the delivered image before input.
            watch = (NativeVisualWatch(bridge, source['sequence'], decision['watch_regions'],
                     timeout_ms=decision.get('watch_timeout_ms', 1000))
                     if 'watch_regions' in decision else None)
            started = time.monotonic_ns()
            alias = f'target_{stage}'
            offset = bridge.mint(alias, source['sequence'], decision['point'], region_size=(24, 14))
            dispatch = bridge.click if interaction == 'click' else bridge.keyboard
            result = dispatch(alias, offset,
                                  tail=paced_text_tail(decision.get('tail', []), args.text_gap_ms))
            row = {'stage': stage, 'interaction': interaction, 'result': result, 'started_ns': started}
            rows.append(row)
            save('actions.json', rows)
            if result['status'] != 'completed':
                if result.get('recovery_required') is True:
                    row['release_observation'] = observe_release_failure(bridge.backend)
                    save('actions.json', rows)
                raise RuntimeError('native action '+result['status']+'; no replay')
            if watch is not None:
                row['visual_watch'] = watch.run(bridge)
                save('actions.json', rows)
            # Same feedback contract as Chromium. Focus changes return a fresh
            # image needing review, not a guessed dialog confirmation.
            row['feedback'] = bridge.feedback(decision['expected_title'], timeout_ms=2000)
            row['ended_ns'] = time.monotonic_ns()
            save('actions.json', rows)
            window = (bridge.backend.targets['app'].id if bridge._focus_within_target()
                      else bridge.focused_client_window())
            if not window:
                raise RuntimeError('no managed focused window for explicit next-stage review')
            row['window_review'] = bridge.review_window(window)
            if row['window_review']['status'] != 'reviewed':
                save('actions.json', rows)
                raise RuntimeError('window review failed; no automatic input or replay')
            source = row['window_review']['observation']
            if args.probe_old_target:
                before = bridge.backend.emissions
                stale = bridge.click(alias, offset)
                row['old_target_probe'] = {'result': stale,
                                           'emissions': bridge.backend.emissions-before}
                if stale['status'] != 'refused' or row['old_target_probe']['emissions']:
                    save('actions.json', rows)
                    raise RuntimeError('old target survived window review')
                row['retired_target_probes'] = []
                for old_alias, old_offset in retired_targets:
                    before = bridge.backend.emissions
                    stale = bridge.click(old_alias, old_offset)
                    probe = {'alias': old_alias, 'result': stale,
                             'emissions': bridge.backend.emissions-before}
                    row['retired_target_probes'].append(probe)
                    if stale['status'] != 'refused' or probe['emissions']:
                        save('actions.json', rows)
                        raise RuntimeError('earlier application target survived window review')
                retired_targets.append((alias, offset))
            row['through_review_ns'] = time.monotonic_ns()
            save('actions.json', rows)
            publish(out/f'source-{stage+1}.json', encoded(source))
            publish(out/f'reply-{stage}.json', encoded({'status': 'boundary', 'stage': stage,
                'decision_sha256': decision_hash, 'action': row, 'observation': source,
                'authority_granted': False, 'task_success': None}))
            print(json.dumps({'stage': stage, 'feedback_status': row['feedback']['status'],
                              'window_review': row['window_review']}), flush=True)
        else:
            raise RuntimeError('bounded action stages exhausted without explicit finish')
        evaluations = {app: suite.evaluate(app, data['output'], data['goal'])
                       for app, data in workloads.items()}
        evaluation = (next(iter(evaluations.values())) if len(evaluations) == 1 else
                      {'success': all(v['success'] for v in evaluations.values()),
                       'applications': evaluations})
        save('evaluation.json', evaluation)
        evaluation = json.loads((out/'evaluation.json').read_text())
        terminal_reply = {'status': 'finished', 'stage': stage,
            'decision_sha256': decision_hash, 'evaluation': evaluation, 'authority_granted': False}
        print(json.dumps({'evaluation': evaluation}), flush=True)
    except Exception:
        failure = traceback.format_exc()
        (out/'error.txt').write_text(failure)
        if decision_hash is not None and not (out/f'reply-{stage}.json').exists():
            terminal_reply = {'status': 'needs_review', 'stage': stage,
                'decision_sha256': decision_hash, 'error': failure, 'actions': rows,
                'authority_granted': False, 'task_success': None}
        raise
    finally:
        cleanup = finish_allocation(out, workloads, bridge, session, terminal_reply)
    if cleanup['status'] != 'completed':
        raise RuntimeError('allocation cleanup needs review; see cleanup-report.json')


if __name__ == '__main__':
    main()
