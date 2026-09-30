"""Read-only audit of expected expiry, retained partial effects and continuation."""
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
        check(member.isfile() and member.name in manifest and member.name not in raw, 'archive member')
        data = archive.extractfile(member).read()
        spec = manifest[member.name]
        check(len(data) == spec['bytes'] and hashlib.sha256(data).hexdigest() == spec['sha256'], 'file hash')
        raw[member.name] = data
check(set(raw) == set(manifest), 'closure')
prefix = 'results-local/guarded-deadline-primary-01/'


def read(name):
    return json.loads(raw[prefix+name])


def reply(n):
    return json.loads(read(f'transport/reply-{n}.json')['result']['content'][0]['text'])


before = json.loads(raw['results-local/guarded-deadline-before-01/before.json'])
check(before['late_text_called'] is True and before['ended_ns'] > before['deadline_ns'], 'before failure')
requests = [read(f'transport/request-{n}.json') for n in range(1,7)]
check([r['tool'] for r in requests] == ['interface_guarded_observe', 'interface_guarded_mint_many',
      'interface_guarded_input', 'interface_guarded_input', 'interface_close', 'interface_results'], 'calls')
check(requests[2]['arguments']['tail'] == [
    {'op':'key_chord','keys':['CTRL','A']}, {'op':'text','text':'t991339-1'},
    {'op':'wait_update','timeout_ms':6000}, {'op':'text','text':'X'}], 'explicit expiry tail')
row = reply(3)
x = row['result']['execution']
check(row['status'] == 'execution_failed' and row['replay_allowed'] is False, 'failure retained')
check(row['result']['recovery_required'] is False, 'release verified by session')
check(row['presentation']['returned'] == 'full' and 'reference_schema' not in row, 'critical full report')
check(x['completed_ops'] == list(range(6)) and x['failed_op'] == 6 and x['program_emissions'] == 25,
      'prefix and no suffix emission')
check(len(x['waits']) == 1 and x['waits'][0]['requested_ms'] == 6000 and
      x['waits'][0]['completed'] is False and x['waits'][0]['update_observed'] is None, 'interrupted wait')
check('expired during wait' in x['error'], 'expiry reason')
release = x['releases'][0]
check(release['verified'] and release['keys_down'] == [] and release['buttons_down'] == [], 'release')
programs = [json.loads(data) for name,data in raw.items()
            if name.startswith(prefix+'server/') and Path(name).name.startswith('program-guarded-')]
expired = [p for p in programs if p['ops'][-2].get('text') == 'X']
check(len(expired) == 1, 'one expired program')
program = expired[0]
check(program['ops'][4:8] == requests[2]['arguments']['tail'], 'raw program/tail identity')
deadline = program['authority']['expires_at_ns']
capture = row['source']['capture_ns']
check(x['waits'][0]['started_ns'] < deadline <= x['waits'][0]['ended_ns'] <= release['monotonic_ns'] < capture,
      'deadline/release/capture order')
metrics = read('expiry-boundaries.json')
check(metrics['deadline_ns'] == deadline and metrics['release_verified_ns'] == release['monotonic_ns'] and
      metrics['capture_started_ns'] == capture and metrics['actual_interrupted_wait_ms'] ==
      (x['waits'][0]['ended_ns']-x['waits'][0]['started_ns'])/1e6, 'boundary identity')
check(metrics['release_verification_after_deadline_ms'] == (release['monotonic_ns']-deadline)/1e6 and
      metrics['post_release_capture_ms'] == (capture-release['monotonic_ns'])/1e6, 'boundary differences')
check(read('transport/review-3.json')['phase'] == 'entered-after-expiry', 'primary partial review')
check(requests[3]['arguments']['alias'] == 'save_a' and requests[3]['arguments']['tail'] ==
      [{'op':'wait_update','timeout_ms':100}] and reply(4)['status'] == 'completed', 'separate Save')
check(reply(5)['status'] == 'closed' and reply(5)['release']['verified'] and
      reply(5)['release']['keys_down'] == [] and reply(5)['release']['buttons_down'] == [], 'close')
historical = reply(6)
check(historical['operation_invoked'] is False and historical['result'] == row['result'] and
      historical['source'] == row['source'], 'unchanged expired history')
images = []
for n in (3,6):
    blocks = [c for c in read(f'transport/reply-{n}.json')['result']['content'] if c['type'] == 'image']
    check(len(blocks) == 1, 'one image')
    images.append(base64.b64decode(blocks[0]['data'], validate=True))
check(images[0] == images[1] and hashlib.sha256(images[0]).hexdigest() ==
      row['source']['native']['artifact']['sha256'], 'historical PNG identity')
records = [json.loads(line) for line in raw[prefix+'independent-submissions.jsonl'].splitlines()]
check(len(records) == 1 and records[0]['exact'] is True and records[0]['task_id'] == 'task-1' and
      records[0]['submitted_values'] == ['t991339-1'], 'independent save')
oracle = read('evaluation.json')
check(oracle['success'] is False and oracle['exact_counts']['task-1'] == 1 and
      oracle['missing'] == [f'task-{i}' for i in range(2,7)], 'scoped oracle')
check(read('transport/exit.json')['code'] == 0, 'transport exit')
check([p['returncode'] for p in read('cleanup.json')] == [0,1,1], 'actual GUI child codes')
events = [json.loads(line) for line in raw[prefix+'transport/host-events.jsonl'].splitlines()]
review = next(e['sequence'] for e in events if e['kind'] == 'review_recorded' and e['attempt'] == 3)
save = next(e['sequence'] for e in events if e['kind'] == 'send_requested' and e['attempt'] == 4)
check(review < save, 'review before continuation')
with tempfile.TemporaryDirectory() as directory:
    for name,data in raw.items():
        if name.startswith(prefix+'transport/'):
            base = name[len(prefix+'transport/'):]
            check(Path(base).name == base, 'flat transport filename')
            (Path(directory)/base).write_bytes(data)
    timing = summarize(directory)
check(timing == read('host-timing.json') and timing['timeline_status'] == 'complete', 'host timing')
plan = json.loads(raw['results-local/guarded-deadline-primary-plan-01.json'])
check(hashlib.sha256(raw['results-local/guarded-deadline-build-01/runtime.pyz']).hexdigest() ==
      plan['runtime_sha256'], 'runtime build')
checks = json.loads(raw['results-local/guarded-deadline-check-01/result.json'])
check(checks['status'] == 'PASS' and all(s['returncode'] == 0 for s in checks['suites']), 'checks')
print(json.dumps({'status':'PASS','files':len(raw),'expiry':'partial failure retained',
                  'continuation':'task1 exact once','six_task_success':False}))
