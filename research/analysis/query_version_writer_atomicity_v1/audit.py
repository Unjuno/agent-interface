import json,pathlib
r=json.loads((pathlib.Path(__file__).parent/'RESULT.json').read_text()); s=r['summary']; d=r['directions']
checks={
'atomic_exact':s['ATOMIC']['unsafe_acceptances']==0 and s['ATOMIC']['false_invalidations']==0,
'membership_first_unsafe':s['MEMBERSHIP_FIRST']['unsafe_acceptances']>0,
'no_version_unsafe':s['NO_VERSION']['unsafe_acceptances']>0,
'version_first_safe':s['VERSION_FIRST']['unsafe_acceptances']==0,
'version_first_overinvalidates':s['VERSION_FIRST']['false_invalidations']>0,
'both_directions':d['insert']>0 and d['remove']>0,
'decision_pass':r['decision']=='PASS_QUERY_VERSION_WRITER_ATOMICITY_SCOPED'}
out={'checks':checks,'pass':all(checks.values())}; print(json.dumps(out,indent=2,sort_keys=True)); raise SystemExit(0 if out['pass'] else 1)
