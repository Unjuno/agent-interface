import json,pathlib
d=json.loads(pathlib.Path('/out/RAW.json').read_text());errors=[];scores=[]
for r in d['rows']:
 mutated=r['id']=='mutated';changed=r['revision_after_read']>r['revision_before_read']
 if changed!=mutated or r['revision_guard_satisfied'] or len(r['modify_events_at_read'])!=r['revision_after_read']:errors.append('notification_guard:'+r['id'])
 scores.append({'id':r['id'],'before':r['revision_before_read'],'after':r['revision_after_read'],'split_satisfied':r['split_satisfied'],'revision_guard_satisfied':r['revision_guard_satisfied']})
if [r['id'] for r in d['rows']]!=['stable','mutated'] or d['errors'] or d['parent_exit']!=0:errors.append('coverage_exit')
print(json.dumps({'decision':'SUPPORT_MODIFY_DETECTION_SCOPED' if not errors else 'FAIL_OR_HOLD','errors':errors,'scores':scores,'scope':'measured setPosition notifications only; not complete generation or atomic snapshot'},indent=2));raise SystemExit(bool(errors))
