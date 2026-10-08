import pathlib,json,hashlib
root=pathlib.Path(__file__).resolve().parent;errors=[]
for item in json.loads((root/'SOURCE_FREEZE.json').read_text(encoding='utf-8-sig')):
    p=pathlib.PureWindowsPath(item['Path']);rel=p.parts[p.parts.index('native-noinput-units-57-4d74')+1:]
    if hashlib.sha256(root.joinpath(*rel).read_bytes()).hexdigest().upper()!=item['Hash']:errors.append('source:'+str(rel))
j=json.loads((root/'first-result.json').read_text(encoding='utf-8-sig'));r=j.get('receipt',{});e=r.get('execution',{})
if j.get('error') or j.get('cleanup_forced') or j.get('xvfb_exit')!=0:errors.append('terminal')
if j['program']['ops']!=[{'op':'wait_update','timeout_ms':1},{'op':'release_all'}]:errors.append('program')
if r.get('status')!='completed' or r.get('recovery_required') is not False:errors.append('native result')
if e.get('completed_ops')!=[0,1] or e.get('program_emissions')!=0 or e.get('emissions')!=0:errors.append('units')
if not e.get('releases') or any(x.get('verified') is not True or x.get('keys_down')!=[] or x.get('buttons_down')!=[] for x in e['releases']):errors.append('owned release')
if len(j['independent_keymap'])!=32 or any(j['independent_keymap']):errors.append('private keymap')
if e.get('ended_ns',0)<e.get('started_ns',1):errors.append('clock')
print(json.dumps(dict(errors=errors,native_runs=j['native_runs'],native_completed_operations=2,tracked_ordinary_emissions=0,scope='same-author saved bytes/private keymap, not hardware/all-button neutrality or task-effect proof'),indent=2));raise SystemExit(bool(errors))
