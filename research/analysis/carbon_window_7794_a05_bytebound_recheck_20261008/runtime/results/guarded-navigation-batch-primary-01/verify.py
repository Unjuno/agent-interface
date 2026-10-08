"""Audit the frozen navigation usability trial; no GUI, input or archived-code execution."""
import base64
import copy
import hashlib
import json
import math
from pathlib import Path
import tarfile

root = Path(__file__).resolve().parent
prefix = 'results-local/guarded-navigation-batch-primary-01/'
manifest = json.loads((root / 'manifest.json').read_text())
raw = {}
def check(value, message):
    if not value:
        raise ValueError(message)
def sha(data):
    return hashlib.sha256(data).hexdigest()
with tarfile.open(root / 'raw.tar.gz') as archive:
    for member in archive.getmembers():
        check(member.isfile() and member.name in manifest and member.name not in raw, 'archive member')
        data = archive.extractfile(member).read()
        check(len(data) == manifest[member.name]['bytes'] and sha(data) == manifest[member.name]['sha256'], 'file identity')
        raw[member.name] = data
check(set(raw) == set(manifest), 'missing files')
def read(name):
    return json.loads(raw[prefix + name])
def request(n):
    return read(f'transport/request-{n}.json')
def reply(n):
    return read(f'transport/reply-{n}.json')
def report(n):
    return json.loads(reply(n)['result']['content'][0]['text'])

plan = json.loads(raw['results-local/guarded-navigation-batch-primary-plan-01.json'])
build = json.loads(raw['results-local/guarded-navigation-batch-build-01/manifest.json'])
check(plan['planned_calls'] == 24 and plan['seed'] == 991337, 'original plan')
check(build['source_revision'] == plan['source'] == '716d25286ec37999d8098cd63bf1731fae0d88d6', 'source revision')
check(sha(raw['results-local/guarded-navigation-batch-build-01/runtime.pyz']) == build['sha256'], 'runtime artifact')
check(len([p for p in raw if p.startswith(prefix + 'transport/request-')]) == 28, 'actual call count')
for n in range(1, 29):
    expected = ('interface_guarded_observe' if n in (1,9,13,19,23) else
                'interface_guarded_mint_many' if n in (2,15) else
                'interface_results' if n in (26,28) else
                'interface_close' if n == 27 else 'interface_guarded_input')
    check(request(n)['tool'] == expected, 'operation sequence')
check(request(15)['arguments']['source_sequence'] == report(14)['source']['sequence'] == 44, 're-grounding source')
events = [json.loads(line) for line in raw[prefix + 'transport/host-events.jsonl'].splitlines()]
check([e['sequence'] for e in events] == list(range(1, len(events) + 1)), 'event ordering')
check(all(math.isfinite(e['host_monotonic_ms']) for e in events), 'finite clock')
check(all(b['host_monotonic_ms'] >= a['host_monotonic_ms'] for a, b in zip(events, events[1:])), 'clock ordering')
def event(kind, n):
    rows = [e for e in events if e['kind'] == kind and e.get('attempt') == n]
    check(len(rows) == 1, 'missing/duplicate event')
    return rows[0]

for n in range(1, 29):
    req, rep, shown = request(n), reply(n), report(n)
    check(req['id'] == rep['id'] == n and req['tool'] == rep['tool'], 'relay identity')
    stages = [event(k, n) for k in ('send_requested', 'reply_available', 'presentation_started', 'presentation_callbacks_completed')]
    check([e['sequence'] for e in stages] == sorted(e['sequence'] for e in stages), 'presentation order')
    for e in stages[1:]:
        check(e['reply_sha256'] == sha(raw[prefix + f'transport/reply-{n}.json']), 'reply event hash')
    for block in rep['result']['content']:
        if block['type'] != 'image':
            continue
        artifact = shown['source']['native']['artifact']
        path = artifact['path'].split('/agent-interface-integrated-main/', 1)[1]
        check(base64.b64decode(block['data'], validate=True) == raw[path] and sha(raw[path]) == artifact['sha256'], 'image parity')
    if req['tool'] != 'interface_guarded_input':
        continue
    original = read('server/' + shown['call_id'] + '/report.json')
    restored = copy.deepcopy(shown)
    if 'reference_schema' in restored:
        check(restored['observation_references'] == {'/observation_report/observation': '/source/native'}, 'reference map')
        check(restored['observation_report']['observation'] == {'observation_ref': '/source/native'}, 'reference marker')
        restored['observation_report']['observation'] = copy.deepcopy(restored['source']['native'])
    presentation = restored.pop('presentation')
    if n == 14:
        check(shown['status'] == 'refused' and shown['result']['input_dispatched'] is False and presentation['returned'] == 'full', 'stale control')
    else:
        check(shown['status'] == 'completed' and presentation['returned'] == 'brief', 'normal input')
        summary = restored['result'].pop('guard_summary')
        guards = original['result']['guard_checks']
        check(summary['checks'] == [{k:g[k] for k in ('stage','observation_sequence','handle','status')} for g in guards], 'guard projection')
        restored['result']['guard_checks'] = guards
        releases = shown['result']['execution']['releases']
        check(releases and all(r['verified'] is True and r['keys_down'] == [] and r['buttons_down'] == [] for r in releases), 'input release')
    check({k:restored[k] for k in original} == original, 'raw report parity')

entered = (3, 6, 10, 16, 20, 24)
saved = (4, 7, 11, 17, 21, 25)
navigation = (5, 8, 12, 18, 22)
destinations = (5, 9, 13, 19, 23)
for i, (enter, save) in enumerate(zip(entered, saved), 1):
    check(request(enter)['arguments']['tail'][1] == {'op':'text','text':f't991337-{i}'}, 'entered value')
    check(event('review_recorded', enter)['sequence'] < event('send_requested', save)['sequence'], 'review before Save')
    for n, phase in ((enter, 'entered'), (save, 'saved')):
        check(read(f'transport/review-{n}.json')['phase'] == phase, 'review phase')
for i, (nav, dest) in enumerate(zip(navigation, destinations), 2):
    args = request(nav)['arguments']
    check(args['interaction'] == 'keyboard' and args['alias'] == 'keyboard_context', 'navigation target')
    check(args['tail'] == [{'op':'key_chord','keys':['CTRL','l']}, {'op':'wait_update','timeout_ms':100},
          {'op':'text','text':read('goal.json')['tasks'][i-1]['url']}, {'op':'key_chord','keys':['ENTER']},
          {'op':'wait_update','timeout_ms':100}], 'frozen navigation tail')
    check(event('review_recorded', dest)['phase'] == 'destination' and event('review_recorded', dest)['sequence'] < event('send_requested', entered[i-1])['sequence'], 'destination review before entry')
    if nav != dest:
        check(event('review_recorded', nav)['phase'] == 'destination-unconfirmed' and request(dest)['tool'] == 'interface_guarded_observe', 'read-only recovery')
for e in events:
    if e['kind'] != 'review_recorded':
        continue
    n = e['attempt']; receipt = read(f'transport/review-{n}.json'); shown = report(n)
    check(receipt['reply_sha256'] == e['reply_sha256'] == sha(raw[prefix + f'transport/reply-{n}.json']), 'review hash')
    check(receipt['call_id'] == e['call_id'] == shown['call_id'] and receipt['source_sequence'] == e['source_sequence'] == shown['source']['sequence'], 'review source')
    check(receipt['images'][0]['sha256'] == sha(base64.b64decode(reply(n)['result']['content'][1]['data'])), 'review image')
    check(event('presentation_callbacks_completed', n)['sequence'] < e['sequence'], 'presentation before review')

oracle = read('evaluation.json')
check(oracle['success'] is True and oracle['record_count'] == 6 and oracle['exact_counts'] == {f'task-{i}':1 for i in range(1,7)} and not oracle['duplicates'] and not oracle['unexpected'] and not oracle['missing'], 'independent scoring')
history = [json.loads(line) for line in raw[prefix + 'submission-history.jsonl'].splitlines()]
check(len(history) == 6 and all(h['task_id'] == f'task-{i}' and h['submitted_values'] == [f't991337-{i}'] for i,h in enumerate(history,1)), 'exact-once history')
check(report(27)['release']['verified'] is True and report(27)['release']['keys_down'] == [] and report(27)['release']['buttons_down'] == [], 'close release')
check(report(27)['session']['observation_sequence'] == report(28)['source']['sequence'] == report(25)['source']['sequence'] == 82, 'no post-close recapture')
check(reply(25)['result']['content'][1] == reply(28)['result']['content'][1] and report(28)['operation_invoked'] is False, 'historical image')
check(report(26)['image_delivery'] == 'omitted_by_request' and report(26)['operation_invoked'] is False and 'presentation' not in report(26), 'full read')
check(read('transport/exit.json')['code'] == 0 and events[-1]['kind'] == 'transport_closed', 'transport terminal')
check(all(type(p['returncode']) is int for p in read('cleanup.json')), 'GUI terminal')
timing = read('host-timing.json')
total = sum(event('reply_available', n)['host_monotonic_ms'] - event('send_requested', n)['host_monotonic_ms'] for n in range(1,29))
check(timing['send_to_reply_total_ms'] == total and timing['call_count'] == 28, 'timing totals')
for name, digest in timing['input_sha256'].items():
    check(sha(raw[prefix + 'transport/' + name]) == digest, 'timing input identity')
print(json.dumps({'status':'PASS', 'files':len(raw), 'six_task_success':True,
      'planned_calls':24, 'actual_calls':28, 'additional_observations':4,
      'candidate_disposition':'HOLD as a default navigation recipe',
      'gui_child_returncodes':[p['returncode'] for p in read('cleanup.json')],
      'send_to_reply_total_ms':total, 'actual_model_tokens':'not measured'}, indent=2))
