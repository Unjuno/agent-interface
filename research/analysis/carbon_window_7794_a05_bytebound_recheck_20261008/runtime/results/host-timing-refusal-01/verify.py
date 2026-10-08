"""Read-only audit of the actual relay refusal and its retained timing report."""
import hashlib
import json
from pathlib import Path
import sys
import tarfile
import tempfile

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root.parents[2]))
from runtime.integration_checks.host_timing import summarize

def check(value, message):
    if not value:
        raise ValueError(message)
manifest = json.loads((root/'manifest.json').read_text())
raw = {}
with tarfile.open(root/'raw.tar.gz') as archive:
    for member in archive.getmembers():
        check(member.isfile() and member.name in manifest and member.name not in raw, 'archive member')
        data = archive.extractfile(member).read()
        check(len(data) == manifest[member.name]['bytes'] and hashlib.sha256(data).hexdigest() == manifest[member.name]['sha256'], 'file hash')
        raw[member.name] = data
check(set(raw) == set(manifest), 'missing files')
prefix = 'results-local/host-timing-refusal-01/'
def read(name):
    return json.loads(raw[prefix+name])
before = read('before.json')
check(before['status'] == 'REPRODUCED' and before['exception'] == 'KeyError' and before['message'] == "'id'", 'original failure')
check(read('transport/reply-1.json') == {'status':'refused','dispatched':False,'next_id':1,'error':'unknown relay tool for selected server kind'}, 'actual refusal')
check([read(f'transport/request-{n}.json')['id'] for n in (1,2,3)] == [1,1,2], 'protocol ID reuse')
check(read('transport/reply-2.json')['id'] == 1 and read('transport/reply-2.json')['status'] == 'returned', 'corrected explicit discovery')
closed = json.loads(read('transport/reply-3.json')['result']['content'][0]['text'])
check(closed['status'] == 'closed' and closed['release_attempted'] is False and closed['connection_close_attempted'] is False, 'backend was not opened')
check(read('transport/exit.json')['code'] == 0, 'transport exit')
with tempfile.TemporaryDirectory() as directory:
    for path, data in raw.items():
        if not path.startswith(prefix+'transport/'):
            continue
        name = path[len(prefix+'transport/'):]
        check(Path(name).name == name, 'flat transport filename')
        (Path(directory)/name).write_bytes(data)
    actual = summarize(directory)
check(actual == read('after.json') and actual['returned_count'] == 3, 'corrected report')
check(actual['calls'][0]['relay_outcome'] == {'status':'refused','dispatched':False,'request_id':1}, 'refusal classification')
checks = json.loads(raw['results-local/host-timing-refusal-check-01/result.json'])
check(checks['status'] == 'PASS' and all(s['returncode'] == 0 for s in checks['suites']), 'integration checks')
print(json.dumps({'status':'PASS', 'actual_replies':3, 'backend_opened':False,
                  'scope':'real relay refusal timing; no GUI or performance claim'}, indent=2))
