"""Independent saved-artifact checks for the finite pointer wake comparison."""
import json
from pathlib import Path
from PIL import Image
from report_pages_v2 import digest
from session_v4 import Decoder

HERE = Path(__file__).resolve().parent
root = HERE / 'results/pointer-wake-comparison-01'
plan = json.loads((root / 'plan.json').read_text())
for name, sha in plan['sources'].items():
    assert digest((HERE / name).read_bytes()) == sha
rows = []
for index, (kind, interrupt, order, seed) in enumerate(plan['allocations']):
    pair = []
    for candidate in order:
        out = root / f'{index}-{candidate}'
        report = json.loads((out / 'report.json').read_text())
        assert report['checks_passed']
        assert (report['kind'], report['interrupt'], report['candidate'], report['seed']) == (kind, interrupt, candidate, seed)
        assert all(v == 'close returned' for v in report['cleanup'].values())
        events = report['events']
        terminal = report['terminal']
        assert [e for e in events if e['event'] == 'terminal'] == [terminal]
        assert terminal['release'] in report['owner_records']
        assert terminal['release']['verified'] and report['physical_up_after_terminal']
        if interrupt:
            cause = terminal['interruption']['record']
            assert cause in report['owner_records'] and cause['reason'] == 'focus_changed'
            assert report['physical_up_after_transfer'] and cause['verified']
            assert report['release_to_terminal_ms'] == (terminal['terminal_ns'] - cause['verified_ns']) / 1e6
        observations = [e for e in events if e['event'] == 'observation']
        decoder = Decoder('live-control')
        for sequence, event in enumerate(observations, 1):
            assert event['sequence'] == sequence
            frame = decoder.accept((out / f'{sequence:03d}.ait').read_bytes())
            with Image.open(out / Path(event['image']).name) as im:
                assert (im.width, im.height, im.mode, im.tobytes()) == (frame.width, frame.height, frame.mode, frame.pixels)
        assert digest((out / '001.png').read_bytes()) == report['initial_png_sha256']
        pair.append(report['initial_png_sha256'])
        rows.append({'kind': kind, 'interrupt': interrupt, 'candidate': candidate,
                     'status': terminal['status'], 'steps_completed': terminal['steps_completed'],
                     'release_to_terminal_ms': report.get('release_to_terminal_ms'),
                     'exact_frames': len(observations), 'moves': report['admitted_moves']})
    assert pair[0] == pair[1]
result = {'success': True, 'audit_sha256': digest(Path(__file__).read_bytes()), 'rows': rows,
          'limits': 'Saved owner/keymap checks and exact image transport; no independent saved document task score or model performance. Close-return records are not independent child-process inventory.'}
(root / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
