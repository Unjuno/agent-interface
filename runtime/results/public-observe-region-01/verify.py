"""Check frozen regression evidence without extracting or executing it."""
import base64
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
    require({m.name for m in members} == set(manifest), 'member names')
    raw = {}
    for member in members:
        require(member.isfile(), 'regular files only')
        data = archive.extractfile(member).read()
        expected = manifest[member.name]
        require(len(data) == expected['bytes'], 'byte count')
        require(hashlib.sha256(data).hexdigest() == expected['sha256'], 'file hash')
        raw[member.name] = data


def load(path):
    return json.loads(raw['results-local/' + path])


def report(path):
    reply = load(path)
    require(reply['status'] == 'returned', 'relay response')
    value = json.loads(next(b['text'] for b in reply['result']['content'] if b['type'] == 'text'))
    return value, reply


old, _ = report('ops-world-primary-02/transport/reply-2.json')
old_result = old['receipt']['source']['raw_report']['result']
require(old_result['error'] == 'INVALID_PROGRAM' and old_result['backend_emissions'] == 0, 'old refusal')
prefix = 'ops-world-primary-03/'
for attempt, index in ((2, 4), (4, 3)):
    shown, reply = report(prefix + f'transport/reply-{attempt}.json')
    recorded = shown['receipt']['source']['raw_report']
    request = load(prefix + f'transport/request-{attempt}.json')['arguments']['program']
    require(recorded['normalization']['source_program'] == request, 'original program retained')
    require(recorded['normalization']['source_operation_indices'] == [index], 'source mapping')
    require(request['ops'][index]['region'] == [0, 0, 640, 360], 'region syntax')
    require('x' not in request['ops'][index], 'unambiguous form')
    require(recorded['result']['status'] == 'completed', 'completed dispatch')
    execution = recorded['result']['execution']
    require(execution['completed_ops'] == list(range(len(request['ops']))), 'operation count unchanged')
    require(execution['observations'][0]['region'] == [0, 0, 640, 360], 'captured region')
    release = execution['releases'][-1]
    require(release['verified'] and release['keys_down'] == [] and release['buttons_down'] == [], 'release')
    image = next(b for b in reply['result']['content'] if b['type'] == 'image')
    digest = hashlib.sha256(base64.b64decode(image['data'])).hexdigest()
    require(digest == execution['observations'][0]['artifact']['sha256'], 'delivered image binding')
negative, _ = report(prefix + 'transport/reply-3.json')
negative = negative['receipt']['source']['raw_report']
require(negative['error'] == 'INVALID_OBSERVATION_REGION' and negative['input_dispatched'] is False, 'negative input refusal')
require(negative['source_operation_index'] == 1, 'negative source location')
closed, _ = report(prefix + 'transport/reply-6.json')
require(closed['status'] == 'closed' and closed['release']['verified'], 'explicit close')
require(load(prefix + 'transport/exit.json')['code'] == 0, 'relay exit')
require(load(prefix + 'app-exit.json')['returncode'] == 0, 'normal application exit')
require(all(p['returncode'] is not None for p in load(prefix + 'cleanup.json')), 'all owned children exited')
require(load(prefix + 'evaluator-report.json')['success'] is False, 'no task success claim')
require(load('observe-region-native-01/result.json')['status'] == 'PASS', 'native checks')
build = load('observe-region-build-01/build.json')
require(hashlib.sha256(raw['results-local/observe-region-build-01/runtime.pyz']).hexdigest() == build['sha256'], 'runtime hash')
for attempt in (1, 2, 3, 4):
    review = load(prefix + f'primary-review-{attempt}.json')
    require(review['reply_sha256'] == hashlib.sha256(raw['results-local/' + prefix + f'transport/reply-{attempt}.json']).hexdigest(), 'review binding')
print(f'PASS: {len(raw)} retained files; public-region motor smoke and refusal control, not task performance')
