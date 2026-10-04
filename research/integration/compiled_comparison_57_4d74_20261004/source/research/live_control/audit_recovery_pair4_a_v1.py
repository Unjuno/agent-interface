"""Verify archived OpenTTD pair 4 A, retaining presentation failure."""
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


def main():
    root = HERE / 'results/recovery-pair4-01/A'
    runtime = root / 'runtime'
    metadata = read(root / 'initial/execution.json')
    assert (metadata['pair'], metadata['arm'], metadata['seed']) == (4, 'A', 204)
    assert metadata['runner_sha256'] == sha(HERE / 'recovery_pair4_v1.py')
    assert metadata['plan_sha256'] == sha(HERE / 'recovery_comparison_plan_v1.json')
    for manifest in (HERE / 'recovery_comparison_plan_v1.json', runtime / 'manifest.json'):
        for path, digest in read(manifest)['sources'].items():
            assert sha(HERE.parent / path) == digest, path
    raw = [json.loads(line) for line in (runtime / 'events.jsonl').read_text().splitlines()]
    segments = []
    for stage in ('initial', 'prepare', 'recover1', 'recover2', 'recover3', 'recover4', 'open', 'build', 'finish'):
        for q in sorted((root / stage).glob('query-*-request.json')):
            segments.append({'request': read(q), 'reply': read(q.with_name(q.name.replace('-request', '-reply')))})
    covered = set()
    for item in segments:
        a, b = item['request']['after'], item['reply']['cursor']
        assert item['reply']['records'] == raw[a:b] and b - a == len(item['reply']['records'])
        covered.update(range(a, b))
    assert covered == set(range(len(raw)))
    stale = read(root / 'prepare/stale-right-report.json')
    assert stale['program_sent'] is False and stale['reason'] == 'own command echo required'
    recovery_reads = []
    queued = read(root / 'prepare/queued-clocks.json')
    own = stale['exchanges'][0]['request']['request_id']
    for index in range(1, 5):
        stage = root / ('recover' + str(index))
        new = read(stage / 'new-slices.json')
        assert len(new) == 1 and 'command' not in new[0]['request']
        assert new[0]['request'] == read(stage / 'query-0-request.json')
        assert new[0]['reply'] == read(stage / 'query-0-reply.json')
        recovery_reads += new
        history = assemble(stale['exchanges'] + recovery_reads)
        assert history == read(stage / 'history.json')
        assert history['review_batch'] == read(stage / 'batch.json')
        tail = new[0]['reply']['records'][-2:]
        if index < 4:
            assert tail == queued[index - 1]['records']
            assert tail[0]['command']['transport_request_id'] != own
        else:
            assert tail[0]['command']['transport_request_id'] == own
            assert tail[1]['event'] == 'clock'
        selected = read(stage / 'result.json')['image']
        assert selected['sequence'] == 2
        assert sha(runtime / selected['relative_path']) == selected['sha256']
    assert read(root / 'open/open-toolbar-source.json') == history['review_batch']
    with Image.open(runtime / '002.png') as picture:
        assert picture.convert('RGB').getbbox() is not None
        image_extrema = picture.convert('RGB').getextrema()
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
        'audit_sha256': sha(Path(__file__)), 'pair': 4, 'arm': 'A',
        'socket_exchanges': len(segments), 'unique_records': len(raw), 'exact_frames': len(observations),
        'recovery_reads': 4, 'recovery_outer_calls_reported': 4, 'sequence_2_rgb_extrema': image_extrema,
        'capture_to_last_terminal_seconds': (terminals[-1]['terminal_ns'] - observations[0]['capture_ns']) / 1e9,
        'capture_to_evaluation_seconds': (raw[-1]['emitted_ns'] - observations[0]['capture_ns']) / 1e9,
        'score': verdict, 'cleanup': cleanup, 'presentation': read(root / 'presentation.json'),
        'paired_effect': None, 'model_performance_qualified': False,
        'scope': 'Saved evidence audited; model receipt and original full-output visibility cannot be proved from runtime logs. Presentation failure retained; no clean rerun.',
        'next': 'Pair 4 B using unchanged runner and canonical save.'}
    (root / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
