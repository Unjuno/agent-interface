"""Read-only byte and outcome checks; never extract or execute archived scripts."""
import hashlib
import json
from pathlib import Path
import tarfile


def require(condition, message):
    if not condition:
        raise ValueError(message)


root = Path(__file__).resolve().parent
manifest = json.loads((root / 'manifest.json').read_text())
with tarfile.open(root / 'raw.tar.gz') as archive:
    members = archive.getmembers()
    require(len(members) == len(manifest), 'member count')
    require({m.name for m in members} == set(manifest), 'member identities')
    raw = {}
    for member in members:
        require(member.isfile(), 'regular files only')
        data = archive.extractfile(member).read()
        require(len(data) == manifest[member.name]['bytes'], 'size')
        require(hashlib.sha256(data).hexdigest() == manifest[member.name]['sha256'], 'hash')
        raw[member.name] = data


def load(name):
    return json.loads(raw['results-local/' + name])


before = load('x11-uncertain-press-before-02/result.json')
require(before['independent_w_down'] is True, 'reproduced held key')
require(before['execution']['releases'][-1]['verified'] is True, 'reproduced false-positive release')
require(before['tracked_keys_after_failure'] == {}, 'lost obligation')
require(load('x11-uncertain-press-before-02/cleanup-key.json')['independent_w_down'] is False, 'before cleanup')
rows = load('x11-uncertain-press-after-01/results.json')
require({(r['pointer'], r['boundary']) for r in rows} == {
    (False, 'send'), (False, 'sync'), (True, 'send'), (True, 'sync')}, 'fault matrix')
require(len(rows) == 4, 'exact four controls')
for row in rows:
    require(row['execution']['completed_ops'] == [] and row['execution']['waits'] == [], 'stop at failed press')
    require(row['execution']['failed_op'] == 0, 'failed input operation')
    require(row['execution']['releases'][-1]['verified'], 'release receipt')
    require(not row['independent_w_down'] and not row['independent_left_down'], 'independent readback')
    require(row['tracked_keys'] == {} and row['tracked_buttons'] == [], 'resolved obligations')
    require(all(p['code'] is not None for p in row['cleanup']), 'owned children reaped')
prefix = 'x11-uncertain-press-mcp-02/'


def mcp(name):
    return json.loads(load(prefix + name)['content'][0]['text'])


failed = mcp('reply-1.json')['receipt']['source']['raw_report']['result']
require(failed['status'] == 'execution_failed', 'MCP retains failure')
require(failed['execution']['completed_ops'] == [], 'no continuation')
require(failed['execution']['releases'][-1]['verified'], 'MCP release')
require(load(prefix + 'witness-1.json')['w_down'] is False, 'witness before next input')
completed = mcp('reply-2.json')['receipt']['source']['raw_report']['result']
require(completed['status'] == 'completed', 'new explicit program')
require(completed['execution']['completed_ops'] == [0, 1, 2, 3], 'new program completed')
require(load(prefix + 'witness-2.json')['w_down'] is False, 'new program released')
require(mcp('close.json')['status'] == 'closed', 'explicit session close')
require(load(prefix + 'client-completed.json')['normal_context_exit'], 'SDK context exit')
require(load('x11-uncertain-press-native-01/result.json')['status'] == 'PASS', 'local suites')
build = load('x11-uncertain-press-build-01/build.json')
require(hashlib.sha256(raw['results-local/x11-uncertain-press-build-01/runtime.pyz']).hexdigest() == build['sha256'], 'built runtime')
print(f'PASS: {len(raw)} retained files; controlled X11 failure/release boundaries, not task or timing performance')
