import pathlib,json,hashlib
root=pathlib.Path(__file__).resolve().parent;errors=[]
for item in json.loads((root/'SOURCE_FREEZE.json').read_text(encoding='utf-8-sig')):
    absolute=pathlib.PureWindowsPath(item['Path']);rel=absolute.parts[absolute.parts.index('motor-native-join-57-4d74')+1:];p=root.joinpath(*rel)
    if hashlib.sha256(p.read_bytes()).hexdigest().upper()!=item['Hash']:errors.append('source:'+str(p.relative_to(root)))
j=json.loads((root/'first-result.json').read_text(encoding='utf-8-sig'));by={r['case']:r['result'] for r in j['rows']}
if by['missing_context']!={'accepted':False,'reason':'missing_context','uncertainty':'OS_UNCONFIRMED'}:errors.append('context gate')
for name,status in [('saved_completed','VERIFIED_EMPTY'),('controlled_release_failure','FAILED')]:
    r=by[name];s=r['state']
    if not r['accepted'] or s['uncertainty']!='OS_UNCONFIRMED' or s['observed_pointer'] is not None:errors.append('uncertainty')
    if s['release']!={'status':status,'retained':True} or s['events']!=[{'type':'RELEASE_TRANSITION','status':status}]:errors.append('release evidence')
    if any('authority' in k for k in s):errors.append('authority field')
if j['native_input_calls']!=0:errors.append('native scope')
print(json.dumps(dict(errors=errors,rows=3,scope='same-author saved custody/type inspection; no native effect/identity/global neutral proof'),indent=2));raise SystemExit(bool(errors))
