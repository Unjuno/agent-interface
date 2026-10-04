import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parent;raw=json.loads((R/'raw.json').read_text(encoding='utf-8-sig'));saved=json.loads((R/'reopen-audit.json').read_text(encoding='utf-8-sig'));out=json.loads((R/'certificate.json').read_text(encoding='utf-8-sig'));F=json.loads((R/'FREEZE.json').read_text());errors=[]
for name,digest in F['files'].items():
    if hashlib.sha256((R/name).read_bytes()).hexdigest()!=digest:errors.append('hash:'+name)
if raw['errors'] or raw['parent_exit']!=0 or saved['errors'] or saved['parent_exit']!=0:errors.append('source_outcome')
source={r['case']:r for r in raw['rows']};endpoints={r['case']:r for r in saved['rows']};seen=[]
for r in out['rows']:
    name=r['scorer_world'];row=source[name];events={e['stage']:e for e in row['events']};view={k:v for k,v in events['before_undo'].items() if k!='stage'};seen.append(view)
    if r['visible_view']!=view:errors.append('view')
    if r['visible_sha256']!=hashlib.sha256(json.dumps(view,sort_keys=True,separators=(',',':')).encode()).hexdigest():errors.append('view_hash')
    if r['verified_after']!=endpoints[name]['reopened_cells'] or r['saved_sha256']!=row['saved_sha256'] or not endpoints[name]['read_only']:errors.append('endpoint')
    if r['verified_after']!=[events['after_undo']['A1'],events['after_undo']['B1']]:errors.append('original_endpoint')
if set(source)!={'single_visible','hidden_attached'} or len(seen)!=2 or seen[0]!=seen[1]:errors.append('alias')
if endpoints['single_visible']['reopened_cells']!=['','PROTECTED'] or endpoints['hidden_attached']['reopened_cells']!=['','']:errors.append('different_footprints')
if out['policy_family']!=['UNDO','DECLINE'] or out['decision']!='SUPPORT_UNCHANGED_VIEW_UNDO_BOUND':errors.append('scope')
print(json.dumps({'decision':'SUPPORT_ANALYTICAL_BOUND_SCOPED' if not errors else 'HOLD','errors':errors,'method':'independent full raw-view reconstruction and saved actual endpoint joins; algebra in report must be reviewed separately'},indent=2));raise SystemExit(bool(errors))
