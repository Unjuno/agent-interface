"""Read-only integrity and observable-boundary checks; no runtime replay."""
from pathlib import Path
import hashlib
import json
from PIL import Image

root = Path(__file__).resolve().parent
manifest = json.loads((root/'FILES.sha256.json').read_bytes())
actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p.name != 'FILES.sha256.json'}
assert actual == set(manifest), 'manifest membership mismatch'
for path, receipt in manifest.items():
    raw = (root/path).read_bytes()
    assert len(raw) == receipt['bytes'] and hashlib.sha256(raw).hexdigest() == receipt['sha256'], path
observations = 0
for arm, expected_exit in [('coast',0), ('guarded',1)]:
    run = root/arm/'run'
    host = json.loads((run/'HOST.json').read_bytes())
    assert host['container_exit'] == expected_exit and host['host_exit'] == 0 and host['reader_alive'] is False
    events = (run/'episode/runtime/events.jsonl').read_bytes().splitlines()
    assert events == (run/'episode/runtime/delivered.jsonl').read_bytes().splitlines()
    for line in events:
        row = json.loads(line)
        if row.get('event') == 'observation':
            with Image.open(run/'episode/runtime'/Path(row['image']).name) as frame:
                assert hashlib.sha256(frame.convert('RGB').tobytes()).hexdigest() == row['frame_rgb_sha256']
            observations += 1
    for relative, expected in json.loads((run/'episode/runtime/sources.json').read_bytes()).items():
        assert hashlib.sha256((root/'source/research'/relative).read_bytes()).hexdigest() == expected
assert (root/'coast/run/episode/report.json').is_file()
assert not (root/'guarded/run/episode/report.json').exists()
assert b'cover validity source health unavailable' in (root/'guarded/run/container.stderr.txt').read_bytes()
diagnostic = json.loads((root/'saved-hud-probe-01/result.json').read_bytes())
assert len(diagnostic) == 4
for result in diagnostic:
    assert result['file'] == result['memory']
    if result['sequence'] == 35:
        assert result['file']['status'] == 'unknown'
        assert all(s['best_score'] == 0 for s in result['file']['detail']['slots'])
    else:
        assert result['sequence'] == 31 and result['file']['status'] == 'observed'
        assert result['file']['value'] == {'health':97,'ammo':47}[result['signal']]
print(json.dumps({'manifest_members':len(manifest), 'rgb_observations':observations, 'scope':'saved integrity only; no causal/task/recovery certificate'}))
