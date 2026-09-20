"""Read-only verification of retained diagnostic bytes; never execute a GUI."""
import base64
import hashlib
import io
import json
from pathlib import Path
import tarfile

root = Path(__file__).resolve().parent
summary = json.loads((root/'RESULT.json').read_text())
archive = (root/'evidence.tar.gz').read_bytes()
assert hashlib.sha256(archive).hexdigest() == summary['archive_sha256']
with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as bundle:
    files = {m.name: bundle.extractfile(m).read() for m in bundle.getmembers() if m.isfile()}
def read(label, name):
    return json.loads(files[label+'/'+name])
assert read('mounted','decision.json') == read('linux','decision.json')
checks = {}
for label in ('mounted','linux'):
    manifest = read(label,'manifest.json')
    actual = {p[len(label)+1:]: hashlib.sha256(data).hexdigest()
              for p,data in files.items() if p.startswith(label+'/') and p != label+'/manifest.json'}
    assert actual == manifest
    effect = read(label,'effect.json')
    assert effect == {'saved': True, 'text': 'log-location-check'}
    original = read(label,'dispatch-reply.json'); retained = read(label,'retained.json')
    first = next(b for b in original['content'] if b['type']=='image')
    second = next(b for b in retained['content'] if b['type']=='image')
    assert first['data'] == second['data']
    assert base64.b64decode(first['data'], validate=True) == files[label+'/image.png']
    assert original['isError'] is False and retained['isError'] is False
    metadata = json.loads(next(b['text'] for b in retained['content'] if b['type']=='text'))
    assert metadata['operation_invoked'] is False
    assert metadata['outcome_summary']['execution_status'] == 'completed'
    assert metadata['outcome_summary']['input_release_verified'] is True
    assert metadata['outcome_summary']['recovery_required'] is False
    assert read(label,'owner-exit.json')['returncode'] == 0
    cleanup = read(label,'cleanup.json')
    assert sorted(r['returncode'] for r in cleanup['tracked_processes']) == [-15,0]
    assert cleanup['descendants_verified'] is False
    checks[label] = {'files_verified': len(actual), 'effect_matches': True, 'reread_image_matches': True}
print(json.dumps({'status':'PASS_RETAINED_RECORDS','checks':checks,
    'scope':'byte/record consistency only; visual interpretation, causation and live process history are not independently proved'}))
