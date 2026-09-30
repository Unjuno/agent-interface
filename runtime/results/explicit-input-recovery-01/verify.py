"""Verify retained construction evidence without extracting/executing it."""
import hashlib
import json
from pathlib import Path
import tarfile


def require(value, message):
    if not value:
        raise ValueError(message)


root = Path(__file__).resolve().parent
manifest = json.loads((root / 'manifest.json').read_text())
with tarfile.open(root / 'raw.tar.gz') as archive:
    members = archive.getmembers()
    require(len(members) == len(manifest), 'member count')
    require({m.name for m in members} == set(manifest), 'member names')
    raw = {}
    for member in members:
        require(member.isfile(), 'regular files only')
        data = archive.extractfile(member).read()
        require(len(data) == manifest[member.name]['bytes'], 'size')
        require(hashlib.sha256(data).hexdigest() == manifest[member.name]['sha256'], 'hash')
        raw[member.name] = data


def load(name):
    return json.loads(raw['results-local/' + name])


def report(prefix, name):
    shown = json.loads(load(prefix + name)['content'][0]['text'])
    return shown.get('receipt', {}).get('source', {}).get('raw_report', shown)


before = 'x11-explicit-recovery-before-01/'
after = 'x11-explicit-recovery-after-01/'
for prefix in (before, after):
    first = report(prefix, 'reply-1.json')
    require(first['result']['status'] == 'execution_failed', 'injected failure')
    require(first['result']['recovery_required'] is True, 'sticky recovery')
    require(first['result']['execution']['releases'][-1]['verified'] is False, 'failed cleanup')
    require(load(prefix + 'witness-1.json')['w_down'] is True, 'independent held key')
    second = report(prefix, 'reply-2.json')
    require(second['result']['error'] == 'INPUT_RECOVERY_REQUIRED', 'normal release program blocked')
    require(load(prefix + 'witness-2.json')['w_down'] is True, 'still held before recovery/close')
    require(load(prefix + 'witness-after-close.json')['w_down'] is False, 'final cleanup')
    require(load(prefix + 'client-completed.json')['normal_context_exit'], 'normal SDK context exit')
    require(all(p['code'] is not None for p in load(prefix + 'cleanup.json')), 'owned child exit')
recovery = report(after, 'recovery.json')
require(recovery['status'] == 'input_recovered', 'explicit recovery')
require(recovery['release']['verified'] and recovery['release']['keys_down'] == [] and recovery['release']['buttons_down'] == [], 'neutral readback')
require(recovery['binding_revision'] == 2 and recovery['session']['recovery_required'] is False, 'new revision')
require(load(after + 'witness-after-recovery.json')['w_down'] is False, 'independent recovery readback before new input')
for name in ('stale-recovery.json', 'stale-program.json'):
    require(report(after, name)['error'] == 'SESSION_BINDING_REVISION_MISMATCH', 'old revision refusal')
require(report(after, 'stale-recovery.json')['release_attempted'] is False, 'no repeat release')
require(report(after, 'post-recovery-observation.json')['status'] == 'returned', 'read-only observation')
new = report(after, 'new-program.json')
require(new['result']['status'] == 'completed' and new['result']['execution']['completed_ops'] == [0, 1, 2, 3], 'new program completed')
require(new['session']['session_id'] == recovery['session']['session_id'], 'same connection owner')
require(load(after + 'witness-after-new-program.json')['w_down'] is False, 'new program released')
retained = report(after, 'retained-recovery.json')
require(retained['operation_invoked'] is False and retained['release'] == recovery['release'], 'historical recovery without repeat')
require(load('explicit-input-recovery-native-01/result.json')['status'] == 'PASS', 'local suites')
build = load('explicit-input-recovery-build-01/build.json')
require(hashlib.sha256(raw['results-local/explicit-input-recovery-build-01/runtime.pyz']).hexdigest() == build['sha256'], 'runtime identity')
print(f'PASS: {len(raw)} files; same-session release recovery and stale-request controls, not task performance')
