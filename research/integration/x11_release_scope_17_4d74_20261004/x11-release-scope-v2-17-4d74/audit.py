import json,pathlib,hashlib
R=pathlib.Path('/data');O=pathlib.Path('/out');P=json.loads((R/'PLAN.json').read_text());F=json.loads((R/'FREEZE.json').read_text());raw=json.loads((R/'candidate-out/RAW.json').read_text());errors=[];rows=[]
if raw['errors'] or raw['source_hashes']!=F['source_hashes']:errors.append('source/native errors')
for p,h in F['source_hashes'].items():
 if hashlib.sha256((R/p).read_bytes()).hexdigest()!=h:errors.append('source hash '+p)
if [r['cell'] for r in raw['rows']]!=P['cells']:errors.append('cell inventory')
for r in raw['rows']:
 e={x['label']:x for x in r['events']};before=e['before_release']['keys'];after=e['after_release']['keys'];receipt=r['release_receipt'];name=r['cell'];code=r['codes']['b' if name=='foreign_b' else 'alt']
 expected_before=[] if name=='neutral' else [code];expected_after=[code] if name=='foreign_b' else []
 if before!=expected_before or after!=expected_after:errors.append('actual keymap '+name)
 if not receipt['verified'] or receipt['keys_down'] or receipt['buttons_down'] or r['backend_tracking_after']:errors.append('scoped release '+name)
 if r['cleanup_keymap'] or r['server_exit']!=0 or r['errors']:errors.append('cleanup '+name)
 if not (e['before_release']['end_ns']<=r['release_start_ns']<=receipt['monotonic_ns']<=r['release_end_ns']<=e['after_release']['start_ns']):errors.append('ordered release '+name)
 rows.append(dict(cell=name,before_keys=before,after_keys=after,scoped_verified=receipt['verified'],release_window_ns=r['release_end_ns']-r['release_start_ns']))
out=dict(errors=errors,rows=rows,disposition='PASS_RELEASE_SCOPE_BOUNDARY' if not errors else 'HOLD_OR_FAIL',scope='Private XTEST server-keyboard state only. Scoped receipt not global neutral, overlapping same key not per-client ownership. No input authority/game usefulness/hardware/deadline/race generalization.')
with (O/'AUDIT.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out));raise SystemExit(bool(errors))
