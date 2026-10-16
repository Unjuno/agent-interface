"""Audit registered first pair, retaining the helper-arm focus interruption."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image
from session_v4 import Decoder
from received_history_v1 import assemble

HERE = Path(__file__).resolve().parent


def read(p):
    return json.loads(p.read_text())


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    cohort = HERE / 'results/recovery-pair1-01'
    rows = {}
    plan = read(HERE / 'recovery_comparison_plan_v1.json')
    assert plan['schedule'][0] == {'pair': 1, 'domain': 'inkscape', 'depth': 1, 'seed': 201, 'order': ['A', 'B']}
    for name, digest in plan['sources'].items():
        assert sha(HERE.parent / name) == digest
    for arm in ('A', 'B'):
        root = cohort / arm
        runtime = root / 'runtime'
        execution = read(root / 'initial/execution.json')
        assert execution['runner_sha256'] == sha(HERE / 'recovery_pair1_v1.py')
        assert execution['plan_sha256'] == sha(HERE / 'recovery_comparison_plan_v1.json')
        assert execution['arm'] == arm and execution['seed'] == 201
        for name, digest in read(runtime / 'sources.json').items():
            assert sha(HERE.parent / name) == digest
        raw = [json.loads(line) for line in (runtime / 'events.jsonl').read_text().splitlines()]
        segments = []
        for stage in ('initial', 'prepare', 'recover', 'move', 'finish'):
            for request in sorted((root / stage).glob('query-*-request.json')):
                segments.append({'request': read(request), 'reply': read(request.with_name(request.name.replace('-request', '-reply')))})
        if arm == 'B':
            drain = read(root / 'recover/drain-report.json')
            assert len(drain['reads']) == 1 and drain['state'] == 'own_clock_received_review_required'
            assert all('command' not in item['request'] for item in drain['reads'])
            segments += drain['reads']
            segments += read(root / 'extra-recovery/report.json')['exchanges']
        covered = set()
        for item in segments:
            a, b = item['request']['after'], item['reply']['cursor']
            assert item['reply']['records'] == raw[a:b]
            assert len(item['reply']['records']) == b - a
            covered.update(range(a, b))
        assert covered == set(range(len(raw)))
        stale = read(root / 'prepare/stale-right-report.json')
        assert stale['program_sent'] is False
        recovery_slices = ([{'request': read(root / 'recover/query-0-request.json'), 'reply': read(root / 'recover/query-0-reply.json')}]
                           if arm == 'A' else read(root / 'recover/drain-report.json')['reads'])
        history = read(root / 'recover/history.json')
        assert history == assemble(stale['exchanges'] + recovery_slices)
        assert read(root / 'move/move-save-source.json') == history['review_batch']
        assert history['review_batch']['cursor'] == 12
        decoder = Decoder('live-control')
        observations = [e for e in raw if e['event'] == 'observation']
        for index, event in enumerate(observations, 1):
            assert event['sequence'] == index
            frame = decoder.accept((runtime / f'{index:03d}.ait').read_bytes())
            with Image.open(runtime / Path(event['image']).name) as im:
                assert (im.width, im.height, im.mode, im.tobytes()) == (frame.width, frame.height, frame.mode, frame.pixels)
        evaluation = raw[-1]
        assert evaluation['event'] == 'independent_evaluation' and evaluation['success'] is True
        rect = ET.parse(runtime / 'shape.svg').getroot().find('{http://www.w3.org/2000/svg}rect')
        assert {k: rect.get(k) for k in evaluation['actual']} == evaluation['actual']
        terminals = [e for e in raw if e['event'] == 'terminal']
        assert all(e['release']['verified'] for e in terminals)
        assert [e['status'] for e in terminals] == (['completed', 'completed'] if arm == 'A' else ['completed', 'needs_decision', 'completed'])
        if arm == 'B':
            assert any(e['reason'] == 'focus_changed' for e in read(runtime / 'owner-events.json'))
            first = read(root / 'move/move-save-report.json')['last_reply']['records']
            assert not any(e['event'] == 'input_admission' for e in first)
        rows[arm] = {'socket_exchanges': len(segments), 'recovery_reads': len(recovery_slices),
                     'unique_records': len(raw), 'exact_frames': len(observations),
                     'first_move_terminal': terminals[1]['status'], 'final_task_success': True,
                     'capture_to_evaluation_seconds': (evaluation['known_ns'] - observations[0]['capture_ns']) / 1e9,
                     'saved_rectangle': evaluation['actual']}
    assert read(cohort / 'A/move/move-save-steps.json') == read(cohort / 'B/move/move-save-steps.json')
    assert read(cohort / 'A/runtime/sources.json') == read(cohort / 'B/runtime/sources.json')
    assert sha(cohort / 'A/runtime/001.png') == sha(cohort / 'B/runtime/001.png')
    result = {'audit_sha256': sha(Path(__file__)), 'pair': 1, 'arms': rows,
              'same_initial_png_steps_runtime_sources': True, 'recovery_call_delta_B_minus_A': 0,
              'full_duration_delta_B_minus_A_seconds': rows['B']['capture_to_evaluation_seconds'] - rows['A']['capture_to_evaluation_seconds'],
              'model_performance_qualified': False, 'qualification_reason': 'exact model identity/configuration unavailable',
              'remaining_scheduled_episodes': 6,
              'decision': 'No call reduction at depth 1. Retain focus interruption and recovery; do not attribute it causally to helper or claim speed benefit.'}
    (cohort / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
