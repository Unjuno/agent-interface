"""Verify both archived OpenTTD pair 3 arms, retaining presentation failure."""
import hashlib
import json
import sys
from pathlib import Path
from PIL import Image
from session_v4 import Decoder
from received_history_v1 import assemble
from pointer_report_view_v1 import unpack

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'openttd_task'))
from guarded_score import score


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(arm):
    root = HERE / 'results/recovery-pair3-01' / arm
    runtime = root / 'runtime'
    metadata = read(root / 'initial/execution.json')
    assert (metadata['pair'], metadata['arm'], metadata['seed']) == (3, arm, 203)
    assert metadata['runner_sha256'] == sha(HERE / 'recovery_pair3_v1.py')
    assert metadata['plan_sha256'] == sha(HERE / 'recovery_comparison_plan_v1.json')
    for manifest in (HERE / 'recovery_comparison_plan_v1.json', runtime / 'manifest.json'):
        for path, digest in read(manifest)['sources'].items():
            assert sha(HERE.parent / path) == digest, path
    raw = [json.loads(line) for line in (runtime / 'events.jsonl').read_text().splitlines()]
    segments = []
    for stage in ('initial', 'prepare', 'recover', 'open', 'build', 'finish'):
        for q in sorted((root / stage).glob('query-*-request.json')):
            segments.append({'request': read(q), 'reply': read(q.with_name(q.name.replace('-request', '-reply')))})
    drain = read(root / 'recover/drain-report.json') if arm == 'B' else {
        'state': 'own_clock_received_review_required',
        'reads': [{'request': read(root / 'recover/query-0-request.json'), 'reply': read(root / 'recover/query-0-reply.json')}],
        'history': read(root / 'recover/history.json')}
    assert drain['state'] == 'own_clock_received_review_required' and len(drain['reads']) == 1
    assert all('command' not in item['request'] for item in drain['reads'])
    if arm == 'B':
        segments += drain['reads']
    covered = set()
    for item in segments:
        a, b = item['request']['after'], item['reply']['cursor']
        assert item['reply']['records'] == raw[a:b] and b - a == len(item['reply']['records'])
        covered.update(range(a, b))
    assert covered == set(range(len(raw)))
    stale = read(root / 'prepare/stale-right-report.json')
    assert stale['program_sent'] is False and stale['reason'] == 'own command echo required'
    assert drain['history'] == assemble(stale['exchanges'] + drain['reads'])
    assert read(root / 'open/open-toolbar-source.json') == drain['history']['review_batch']
    own = stale['exchanges'][0]['request']['request_id']
    assert drain['reads'][-1]['reply']['records'][-2]['command']['transport_request_id'] == own
    for stage, name in [('open', 'open-toolbar'), ('build', 'build-road')]:
        report = read(root / stage / (name + '-report.json'))
        assert unpack(read(root / stage / 'result.json')['view']) == report
        selected = report['image']
        assert sha(runtime / selected['relative_path']) == selected['sha256']
    assert [e['id'] for e in raw if e['event'] == 'accepted'] == ['advance', 'open-toolbar', 'build-road']
    terminals = [e for e in raw if e['event'] == 'terminal']
    assert [e['id'] for e in terminals] == ['advance', 'open-toolbar', 'build-road']
    assert all(e['status'] == 'completed' and e['release']['verified'] for e in terminals)
    decoder = Decoder('live-control')
    observations = [e for e in raw if e['event'] == 'observation']
    for index, event in enumerate(observations, 1):
        assert event['sequence'] == index
        frame = decoder.accept((runtime / f'{index:03d}.ait').read_bytes())
        with Image.open(runtime / Path(event['image']).name) as im:
            assert (im.width, im.height, im.mode, im.tobytes()) == (frame.width, frame.height, frame.mode, frame.pixels)
    evidence = read(runtime / 'evaluation.json')
    verdict = score(evidence['observation'], evidence['baseline'])
    assert verdict['success'] and raw[-1]['success']
    cleanup = read(runtime / 'cleanup.json')
    assert cleanup['all_owned_processes_exited'] and cleanup['save_unchanged']
    result = {
        'audit_sha256': sha(Path(__file__)), 'pair': 3, 'arm': arm,
        'socket_exchanges': len(segments), 'unique_records': len(raw), 'exact_frames': len(observations),
        'recovery_reads': 1, 'recovery_outer_calls_reported': 1,
        'capture_to_last_terminal_seconds': (terminals[-1]['terminal_ns'] - observations[0]['capture_ns']) / 1e9,
        'capture_to_evaluation_seconds': (raw[-1]['emitted_ns'] - observations[0]['capture_ns']) / 1e9,
        'score': verdict, 'cleanup': cleanup, 'presentation': read(root / 'presentation.json'),
        'paired_effect': None, 'model_performance_qualified': False,
        'scope': 'Saved evidence audited; model receipt and original full-output visibility cannot be proved from runtime logs. Presentation failure retained; no clean rerun.',
        'next': 'Pair 4 A then B; retain all pair 3 outcomes.'}
    (root / 'paired-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    results = {arm: audit(arm) for arm in ('A', 'B')}
    cohort = HERE / 'results/recovery-pair3-01'
    for relative in ('runtime/001.png', 'open/open-toolbar-steps.json', 'build/build-road-steps.json'):
        assert (cohort / 'A' / relative).read_bytes() == (cohort / 'B' / relative).read_bytes(), relative
    assert read(cohort / 'A/runtime/manifest.json') == read(cohort / 'B/runtime/manifest.json')
    result = {
        'audit_sha256': sha(Path(__file__)), 'arms': results,
        'initial_png_steps_runtime_manifest_equal': True,
        'recovery_outer_calls_delta_B_minus_A': 0,
        'recovery_socket_reads_delta_B_minus_A': 0,
        'capture_to_evaluation_delta_B_minus_A_seconds': results['B']['capture_to_evaluation_seconds'] - results['A']['capture_to_evaluation_seconds'],
        'qualification': 'Unqualified: B presentation overflow and cross-turn review differ; exact model configuration unavailable. Elapsed difference is not a causal helper effect.'}
    (cohort / 'pair-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

