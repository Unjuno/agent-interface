"""Check retained bytes and scoped observations, without executing/extracting raw data."""
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
        require(member.isfile(), 'only regular files')
        data = archive.extractfile(member).read()
        expected = manifest[member.name]
        require(len(data) == expected['bytes'], 'byte count')
        require(hashlib.sha256(data).hexdigest() == expected['sha256'], 'hash')
        raw[member.name] = data


def load(name):
    return json.loads(raw['results-local/' + name])


rows = load('private-x11-readiness-check-01/results.json')
require(len(rows) == 3, 'three independent sessions')
for row in rows:
    require(row['readiness']['managed_and_viewable'], 'readiness')
    require('Procedural Operations World' in row['windows'], 'app listed')
    require(all(p['code'] is not None for p in row['cleanup']), 'cleanup')
require(rows[2]['stopped_manager_refused'], 'stopped manager control')
require(rows[2]['exited_manager_refused'], 'exited manager control')
require(rows[2]['remaining_probes'] == [], 'no probe leak')
require(load('private-x11-readiness-native-01/result.json')['status'] == 'PASS', 'native checks')
prefix = 'ops-world-primary-02/'


def report(attempt):
    reply = load(prefix + f'transport/reply-{attempt}.json')
    require(reply['status'] == 'returned', 'returned relay result')
    return json.loads(next(b['text'] for b in reply['result']['content'] if b['type'] == 'text'))


refused = report(2)['receipt']['source']['raw_report']['result']
require(refused['status'] == 'refused' and refused['backend_emissions'] == 0, 'retained input-free refusal')
require(refused['validation_operation_index'] == 4, 'observe shape refusal')
for attempt in (3, 4, 5):
    result = report(attempt)['receipt']['source']['raw_report']['result']
    require(result['status'] == 'completed', 'completed explicit input')
    release = result['execution']['releases'][-1]
    require(release['verified'] and not release['keys_down'] and not release['buttons_down'], 'release')
require(report(6)['status'] == 'closed', 'explicit close')
require(load(prefix + 'transport/exit.json')['code'] == 0, 'relay exit')
require(load(prefix + 'app-exit.json')['returncode'] == 0, 'normal app exit')
require(load(prefix + 'evaluator-report.json')['success'] is False, 'no task success claim')
require(load(prefix + 'plan.json')['fixed_step'] is False, 'real-time mode')
for attempt in (1, 2, 3, 4):
    review = load(prefix + f'primary-review-{attempt}.json')
    data = raw['results-local/' + prefix + f'transport/reply-{attempt}.json']
    require(review['reply_sha256'] == hashlib.sha256(data).hexdigest(), 'review binding')
print(f'PASS: {len(raw)} retained files; scoped readiness and motor smoke, no task-performance claim')
