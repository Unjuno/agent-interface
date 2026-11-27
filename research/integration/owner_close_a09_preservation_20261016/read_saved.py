"""Saved-byte checks only. Never import owner/candidate or start any GUI/runtime."""
import copy, hashlib, json, sys
from pathlib import Path

def sha(b):
    return hashlib.sha256(b).hexdigest()

def check(data, index):
    if not set(data) == set(index):
        raise AssertionError('saved evidence check failed')
    for name, pin in index.items():
        if not (sha(data[name]) == pin['sha256'] and len(data[name]) == pin['bytes']):
            raise AssertionError(name)

def main():
    q = Path(__file__).resolve().parent
    r = q.parents[2]
    meta = json.loads((q / 'original-blobs.json').read_text())
    p = r / meta['original_prefix']
    data = {name: (p / name).read_bytes() for name in meta['files']}
    check(data, meta['files'])
    missing = []
    manifest = {}
    for line in data['SHA256SUMS'].decode().splitlines():
        pin, name = line.split('  ', 1)
        if not name not in manifest:
            raise AssertionError('saved evidence check failed')
        manifest[name] = pin
        if name not in data:
            missing.append(name)
        elif not sha(data[name]) == pin:
            raise AssertionError(name)
    if not missing == ['RUNNER/BUILD.log']:
        raise AssertionError(missing)
    if not set(data) == set(manifest) - set(missing) | {'SHA256SUMS'}:
        raise AssertionError('saved evidence check failed')
    freeze = json.loads(data['FREEZE.json'])
    raw = json.loads(data['results/A09/RAW.json'])
    if not sha(data['SOURCE/audit.py']) == freeze['auditor_sha256']:
        raise AssertionError('saved evidence check failed')
    if not sha(data['results/A09/RAW.json']) == '8b0ee889c50ad2bb69470bf1faf0e55ff21b81660c72dc3e68dd17e25608eb69':
        raise AssertionError('saved evidence check failed')
    ns = {'__name__': 'saved_audit_only'}
    exec(compile(data['SOURCE/audit.py'], 'retained-audit.py', 'exec'), ns)
    evaluate = lambda value: ns['evaluate'](value, freeze, p / 'SOURCE', p / 'SOURCE/candidate.py')
    result = evaluate(raw)
    if not result['decision'] == 'PASS_METHOD_SCOPED':
        raise AssertionError(result)
    mutations = []
    for field, value in [('observer_key_up', False), ('client_events', []), ('owner_records', [])]:
        changed = copy.deepcopy(raw)
        changed[field] = value
        if not evaluate(changed)['decision'] != 'PASS_METHOD_SCOPED':
            raise AssertionError('saved evidence check failed')
        mutations.append(field)
    changed = copy.deepcopy(raw)
    changed['cleanup']['owner_thread_alive'] = True
    if not evaluate(changed)['decision'] != 'PASS_METHOD_SCOPED':
        raise AssertionError('saved evidence check failed')
    mutations.append('owner_thread_alive')
    changed = dict(data)
    changed['results/A09/RAW.json'] += b' '
    try:
        check(changed, meta['files'])
    except AssertionError:
        mutations.append('raw_byte_tamper')
    else:
        raise AssertionError('raw tamper accepted')
    changed = dict(data)
    changed.pop('REPORT.md')
    try:
        check(changed, meta['files'])
    except AssertionError:
        mutations.append('missing_original')
    else:
        raise AssertionError('missing original accepted')
    result = dict(source_head=meta['head_sha'], preserved_original_files=len(data), original_manifest_entries=len(manifest), original_manifest_complete=False, missing_original_files=missing, saved_method_checks=result, mutations_rejected=mutations, scope='Preservation/readback only; no producer, WSLc, Docker, display, native input, game or model. Historical scoped audit is not current-source qualification.', optimize=sys.flags.optimize)
    Path(sys.argv[1]).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))
if __name__ == '__main__':
    main()
