"""Audit successful model-reviewed servo integration and actual blocked-output fault."""
import json
from pathlib import Path
from PIL import Image
from servo_review_v1 import build
from report_pages_v2 import digest
from session_v4 import Decoder
from score_drag_v1 import score

HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def frames(root, events):
    decoder = Decoder('live-control')
    observations = [e for e in events if e['event'] == 'observation']
    for i, e in enumerate(observations, 1):
        assert e['sequence'] == i
        frame = decoder.accept((root / f'{i:03d}.ait').read_bytes())
        with Image.open(root / Path(e['image']).name) as im:
            assert (im.width, im.height, im.mode, im.tobytes()) == (frame.width, frame.height, frame.mode, frame.pixels)
    return observations


def main():
    root = HERE / 'results/cause-servo-live-02'
    runtime = root / 'runtime'
    for name, sha in read(root / 'initial/plan.json')['sources'].items():
        assert digest((HERE / name).read_bytes()) == sha
    for name, sha in read(runtime / 'sources.json').items():
        assert digest((HERE.parent / name).read_bytes()) == sha
    raw = [json.loads(line) for line in (runtime / 'events.jsonl').read_text().splitlines()]
    covered, exchanges = set(), 0
    for stage in ('initial', 'servo', 'save', 'finish'):
        for path in sorted((root / stage).glob('query-*-request.json')):
            q, reply = read(path), read(path.with_name(path.name.replace('-request', '-reply')))
            a, b = q['after'], reply['cursor']
            assert reply['status'] == 'boundary' and b - a == len(reply['records'])
            assert reply['records'] == raw[a:b] and not covered.intersection(range(a, b))
            covered.update(range(a, b))
            exchanges += 1
    assert covered == set(range(len(raw)))
    attention = {}
    for stage in ('servo', 'save'):
        receipt = read(root / stage / 'receipt.json')
        assert build((root / stage / 'report.json').read_bytes()) == receipt
        terminal = read(root / stage / 'report.json')['terminal']
        if stage == 'servo':
            assert receipt['format'] == 'servo-review-v1' and receipt['status'] == terminal['status']
        else:
            assert receipt['format'] == 'decision-receipt-v4' and receipt['program_binding']['terminal'] == terminal
        assert terminal['status'] == 'completed' and terminal['interruption'] is None
        attention[stage] = len(receipt.get('attention', []))
    feedback = [e for e in raw if e['event'] == 'servo_feedback']
    assert [e['reason'] for e in feedback] == ['correct', 'local_goal_reached']
    assert feedback[-1]['tracking']['delta'] == [20, 0]
    continuations = [e for e in raw if e.get('continuation') is True]
    assert len(continuations) == 1 and continuations[0]['payload'] == {'x': 648, 'y': 391}
    observations = frames(runtime, raw)
    strict = read(root / 'strict-score.json')
    assert all(strict[k] == v for k, v in score(runtime / 'shape.svg').items())
    assert strict['success'] and strict['svg_sha256'] == digest((runtime / 'shape.svg').read_bytes())
    fault_root = HERE / 'results/cause-servo-focus-01'
    fault = read(fault_root / 'report.json')
    for name, sha in fault['sources'].items():
        assert digest((HERE / name).read_bytes()) == sha
    assert fault['success'] and fault['physical_release_while_output_blocked']
    terminals = [e for e in fault['events'] if e['event'] == 'terminal']
    assert terminals[0]['status'] == 'needs_decision' and terminals[0]['steps_completed'] == 0
    assert terminals[0]['interruption']['record'] in fault['owner_records']
    assert terminals[0]['decision_reason'] == 'focus_changed'
    assert not any(e['event'] == 'servo_feedback' or e.get('continuation') for e in fault['events'])
    assert terminals[1]['status'] == 'completed' and terminals[1]['interruption'] is None
    fault_frames = frames(fault_root, fault['events'])
    assert all(t['release']['verified'] for t in terminals)
    assert all(v == 'close returned' for v in fault['cleanup'].values())
    accepted = next(e for e in raw if e['event'] == 'accepted' and e['id'] == 'servo')
    terminal = next(e for e in raw if e['event'] == 'terminal' and e['id'] == 'servo')
    result = {'audit_passed': True, 'audit_sha256': digest(Path(__file__).read_bytes()),
              'live_events': len(raw), 'socket_exchanges': exchanges, 'live_exact_frames': len(observations),
              'fault_exact_frames': len(fault_frames), 'task_score': strict,
              'servo_accept_to_terminal_ms': (terminal['terminal_ns'] - accepted['accepted_ns']) / 1e6,
              'capture_to_evaluation_seconds': (raw[-1]['known_ns'] - observations[0]['capture_ns']) / 1e9,
              'receipt_attention_counts': attention, 'fault_cause_preserved': True,
              'servo_card_bytes': len(json.dumps(read(root / 'servo/receipt.json')).encode()),
              'limits': 'One familiar-layout self-use plus one scripted fault. Runtime timing excludes model and save. Typed servo card used; save retains detailed fallback. Not complete schema validation. No population speed/token or broad generalization claim.'}
    (root / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
