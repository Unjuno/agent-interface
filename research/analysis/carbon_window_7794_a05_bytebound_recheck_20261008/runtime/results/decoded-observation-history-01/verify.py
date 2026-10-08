"""Verify the scoped evidence without executing archived code or GUI input."""
import base64
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
        check(member.isfile() and member.name in manifest and member.name not in raw, 'member')
        data = archive.extractfile(member).read()
        spec = manifest[member.name]
        check(len(data) == spec['bytes'] and hashlib.sha256(data).hexdigest() == spec['sha256'], 'hash')
        raw[member.name] = data
check(set(raw) == set(manifest), 'closure')
prefix = 'results-local/decoded-history-primary-01/'


def read(name):
    return json.loads(raw[prefix+name])


def reply(n):
    return json.loads(read(f'transport/reply-{n}.json')['result']['content'][0]['text'])


requests = [read(f'transport/request-{n}.json') for n in range(1, 9)]
check([r['tool'] for r in requests] == ['interface_guarded_observe']*3 +
      ['interface_guarded_mint_many', 'interface_guarded_input', 'interface_guarded_input',
       'interface_close', 'interface_results'], 'exact calls')
check([reply(n)['source']['sequence'] for n in (1, 2, 3)] == [1, 2, 3], 'new observations')
check(requests[3]['arguments']['source_sequence'] == 1 and reply(4)['status'] == 'minted' and
      reply(4)['session']['observation_sequence'] == 3, 'old-source mint without capture')
check(requests[4]['arguments']['tail'][1] == {'op':'text', 'text':'t991338-1'}, 'entered value')
check(read('transport/review-5.json')['phase'] == 'entered', 'entered review')
check(read('transport/review-6.json')['phase'] == 'saved', 'saved review')
for n in (5, 6):
    row = reply(n)
    check(row['status'] == 'completed' and row['result']['recovery_required'] is False, 'input result')
    releases = row['result']['execution']['releases']
    check(releases and all(r['verified'] and r['keys_down'] == [] and r['buttons_down'] == []
                          for r in releases), 'input release')
check(reply(7)['status'] == 'closed' and reply(7)['release']['verified'] and
      reply(7)['release']['keys_down'] == [] and reply(7)['release']['buttons_down'] == [], 'close')
check(reply(8)['operation_invoked'] is False and reply(8)['source'] == reply(1)['source'], 'historical source')
images = []
for n in (1, 8):
    content = read(f'transport/reply-{n}.json')['result']['content']
    blocks = [c for c in content if c['type'] == 'image']
    check(len(blocks) == 1, 'one image')
    images.append(base64.b64decode(blocks[0]['data'], validate=True))
check(images[0] == images[1] and hashlib.sha256(images[0]).hexdigest() ==
      reply(1)['source']['native']['artifact']['sha256'], 'historical pixels')
records = [json.loads(line) for line in raw[prefix+'independent-submissions.jsonl'].splitlines()]
check(len(records) == 1 and records[0]['exact'] is True and records[0]['task_id'] == 'task-1'
      and records[0]['submitted_values'] == ['t991338-1'], 'independent exact-once save')
oracle = read('evaluation.json')
check(oracle['success'] is False and oracle['exact_counts']['task-1'] == 1 and
      oracle['missing'] == [f'task-{i}' for i in range(2,7)], 'scoped oracle')
check(read('transport/exit.json')['code'] == 0, 'transport exit')
check([p['returncode'] for p in read('cleanup.json')] == [0,1,1], 'actual child exits')
with tempfile.TemporaryDirectory() as directory:
    for name, data in raw.items():
        if name.startswith(prefix+'transport/'):
            basename = name[len(prefix+'transport/'):]
            check(Path(basename).name == basename, 'flat transport')
            (Path(directory)/basename).write_bytes(data)
    timing = summarize(directory)
check(timing == read('host-timing.json') and timing['timeline_status'] == 'complete', 'timing')
events = [json.loads(line) for line in raw[prefix+'transport/host-events.jsonl'].splitlines()]
review = next(e['sequence'] for e in events if e['kind'] == 'review_recorded' and e['attempt'] == 5)
save = next(e['sequence'] for e in events if e['kind'] == 'send_requested' and e['attempt'] == 6)
check(review < save, 'review precedes Save')
for trial, status in [('01','FAIL'),('02','PASS')]:
    checks = json.loads(raw[f'results-local/decoded-history-check-{trial}/result.json'])
    check(checks['status'] == status, 'preserved test outcome')
artifact = raw['results-local/decoded-history-build-01/runtime.pyz']
plan = json.loads(raw['results-local/decoded-history-primary-plan-01.json'])
check(hashlib.sha256(artifact).hexdigest() == plan['artifact_sha256'], 'build identity')
rows = json.loads(raw['results-local/decoded-history-memory-01/summary.json'])['rows']
check(len(rows) == 6 and all(r['old_pixel_parity'] == [True]*3 for r in rows), 'memory parity')
for pair in range(3):
    arms = {r['mode']:r for r in rows if r['pair'] == pair}
    check(set(arms) == {'dict','bounded'}, 'paired modes')
    for mode, row in arms.items():
        original = json.loads(raw[f'results-local/decoded-history-memory-01/{pair}-{mode}.stdout.json'])
        check(row == dict(original, pair=pair), 'raw measurement identity')
    check(arms['bounded']['samples'][-1]['rss_kib'] < arms['dict']['samples'][-1]['rss_kib'], 'retained RSS comparison')
print(json.dumps({'status':'PASS', 'files':len(raw), 'primary_scope':'task-1 only',
                  'six_task_success':False, 'memory_scope':'isolated retention loop'}))
