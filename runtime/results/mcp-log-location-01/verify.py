"""Read-only verification of retained diagnostic bytes; never execute a GUI."""
import base64
import copy
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

def normalize_run_expiry(program):
    normalized = copy.deepcopy(program)
    authority = normalized.get('authority')
    if not isinstance(authority, dict):
        raise AssertionError('program authority is missing')
    expiry = authority.get('expires_at_ns')
    if not isinstance(expiry, int) or expiry < 0:
        raise AssertionError('invalid program lease expiry')
    authority['expires_at_ns'] = 0
    return normalized

def verify_dispatch_binding(decision, request, retained_arguments):
    program = request.get('program')
    if not isinstance(program, dict):
        raise AssertionError('dispatch request has no program')
    source = decision.get('source', {})
    if request.get('current_observation_seq') != source.get('observation_seq'):
        raise AssertionError('dispatch observation sequence differs from decision')
    if request.get('current_binding_revision') != source.get('binding_revision'):
        raise AssertionError('dispatch binding revision differs from decision')
    if decision.get('authority', {}).get('expires_at_ns') != 0:
        raise AssertionError('decision template must use the zero expiry placeholder')
    if program.get('authority', {}).get('expires_at_ns', 0) <= 0:
        raise AssertionError('dispatch request has no per-run lease expiry')
    if normalize_run_expiry(program) != normalize_run_expiry(decision):
        raise AssertionError('dispatched program differs from decision template')
    if retained_arguments != request:
        raise AssertionError('retained call arguments differ from dispatch request')

def expect_binding_rejected(decision, request, retained_arguments):
    try:
        verify_dispatch_binding(decision, request, retained_arguments)
    except (AssertionError, KeyError, TypeError):
        return
    raise AssertionError('binding verifier accepted a corrupted record')

assert read('mounted','decision.json') == read('linux','decision.json')
checks = {}
binding_mutations_checked = False
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
    decision = read(label,'decision.json')
    request = read(label,'dispatch-request.json')
    retained_call = metadata['retained_call']
    assert retained_call['operation'] == 'dispatch'
    verify_dispatch_binding(decision, request, retained_call['arguments'])
    if not binding_mutations_checked:
        bad_request = copy.deepcopy(request)
        bad_request['program']['ops'][4]['text'] = 'mixed-allocation'
        expect_binding_rejected(decision, bad_request, bad_request)
        bad_retained = copy.deepcopy(retained_call['arguments'])
        bad_retained['program']['ops'][4]['text'] = 'edited-retained-call'
        expect_binding_rejected(decision, request, bad_retained)
        bad_sequence = copy.deepcopy(request)
        bad_sequence['current_observation_seq'] += 1
        expect_binding_rejected(decision, bad_sequence, bad_sequence)
        binding_mutations_checked = True
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
    'dispatch_binding':'PASS', 'binding_mutation_challenges':3,
    'scope':'byte/record consistency only; visual interpretation, causation and live process history are not independently proved'}))
