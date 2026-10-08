"""Read-only verification; never extract or execute retained sources."""
import hashlib
import json
from pathlib import Path
import tarfile

def require(value, message):
    if not value:
        raise ValueError(message)

root = Path(__file__).resolve().parent
manifest = json.loads((root / 'manifest.json').read_text())
raw = {}
with tarfile.open(root / 'raw.tar.gz') as archive:
    members = archive.getmembers()
    require(len(members) == len(manifest), 'member count')
    require({m.name for m in members} == set(manifest), 'member identity')
    for member in members:
        require(member.isfile(), 'regular files only')
        data = archive.extractfile(member).read()
        require(len(data) == manifest[member.name]['bytes'], 'size')
        require(hashlib.sha256(data).hexdigest() == manifest[member.name]['sha256'], 'hash')
        raw[member.name] = data

prefix = 'results-local/recovery-capture-primary-01/'
def load(name):
    return json.loads(raw[prefix + name])

reports = []
tools = []
for n in range(1, 7):
    request = load(f'host/request-{n}.json')
    reply = load(f'host/reply-{n}.json')
    require(request['id'] == reply['id'] == n, 'request/reply identity')
    require(request['tool'] == reply['tool'], 'tool identity')
    tools.append(request['tool'])
    shown = json.loads(reply['result']['content'][0]['text'])
    reports.append(shown.get('receipt', {}).get('source', {}).get('raw_report', shown))
    if n < 6:
        review = load(f'primary-review-{n}.json')
        require(review['reply_sha256'] == hashlib.sha256(raw[prefix + f'host/reply-{n}.json']).hexdigest(), 'review binding')
        require(bool(review['reason']), 'review reason')
require(tools == ['interface_observe', 'interface_dispatch', 'interface_recover_input',
                  'interface_dispatch', 'interface_dispatch', 'interface_close'], 'explicit call order')
require(len({r['session']['session_id'] for r in reports}) == 1, 'same session')
failed = reports[1]['result']
require(failed['status'] == 'execution_failed' and failed['recovery_required'], 'failed input')
require(failed['execution']['releases'][0]['keys_down'] == ['w'], 'unreleased W')
recovery = reports[2]
require(recovery['status'] == 'input_recovered' and recovery['binding_revision'] == 2, 'recovered revision')
require(recovery['release']['verified'] and recovery['release']['keys_down'] == [] and recovery['release']['buttons_down'] == [], 'neutral input')
require(recovery['task_success'] is None and recovery['replay_allowed'] is False, 'no semantic completion or replay grant')
require(recovery['observation_report']['status'] == 'returned', 'bundled capture')
require(recovery['observation_report']['observation']['capture_started_ns'] >= recovery['release']['monotonic_ns'], 'capture after release')
require(any(c['type'] == 'image' for c in load('host/reply-3.json')['result']['content']), 'native image delivery')
for index in (3, 4):
    require(reports[index]['result']['status'] == 'completed', 'new program completion')
    require(reports[index]['session']['binding_revision'] == 2, 'new revision')
require(reports[5]['status'] == 'closed' and reports[5]['release']['verified'], 'explicit close')
require(load('saved.json')['count'] == 2, 'saved count')
require([(e['key'], e['count']) for e in load('events.json')] == [('w', 1), ('w', 2), ('s', 2)], 'application effects')
require(load('host/exit.json')['code'] == 0, 'relay normal exit')
require(all(p['returncode'] is not None for p in load('cleanup.json')), 'owned processes reaped')
archive_bytes = raw['results-local/recovery-capture-build-01/runtime.pyz']
require(hashlib.sha256(archive_bytes).hexdigest() == '7962f327fad5d9ca63273c059e23c98186cdc7713766431f6d0418e97c987591', 'exercised runtime identity')
print(f'PASS: {len(raw)} files; primary recovery, reviewed continuation, saved Count 2; no performance claim')
