import hashlib,json,pathlib,sys
p=pathlib.Path(__file__).resolve().parent; rp=pathlib.Path(sys.argv[1]); raw=json.loads(rp.read_text()); t=raw.get('terminal') or {}; rel=t.get('release') or {}; owner=raw.get('owner_records') or []; events=raw.get('events') or []
refusal='distinct resolved keycodes required for up_batch' in str(t.get('error'))
admissions=sum(1 for x in owner if x.get('event')=='input_admission')
checks={'candidate_terminal_recorded':t.get('event')=='terminal','candidate_alias_refusal_observed':refusal,'both_alias_downs_admitted':admissions==2,'terminal_failed':t.get('status')=='failed','cleanup_verified':rel.get('verified') is True,'xvfb_neutral':raw.get('keymap_after') is False,'xvfb_exited':raw.get('xvfb_exit')==0}
if refusal and admissions==2:
 outcome='PASS_METHOD_SCOPED' if all(checks[k] for k in ['terminal_failed','cleanup_verified','xvfb_neutral','xvfb_exited']) else 'FAIL'
else: outcome='STOP'
res={'schema':'issue59-a09-independent-audit-v2','outcome':outcome,'checks':checks,'not_exercised_reason':None if refusal else t.get('error'),'raw_sha256':hashlib.sha256(rp.read_bytes()).hexdigest()}
(p/'results/A09_AUDIT.json').write_text(json.dumps(res,indent=2,sort_keys=True)+'\n'); print(json.dumps(res,sort_keys=True))
