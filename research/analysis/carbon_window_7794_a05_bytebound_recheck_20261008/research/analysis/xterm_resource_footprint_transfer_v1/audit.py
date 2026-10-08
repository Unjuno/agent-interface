import json, pathlib
root=pathlib.Path(__file__).parent
r=json.loads((root/'RESULT.json').read_text())
c=r['classifications']; a=r['agreement']; p=r['pinned']
checks={
  'pinned_report': p['report_blob']=='eb7c3fd431b333b7b5ee9c8958d59eb56c1d5094',
  'pinned_result': p['result_blob']=='5286763730c8442bf6b43cbc1038c655a46121fa',
  'independent_eligible': c['independent']=='OVERLAP_ELIGIBLE',
  'shared_conflict': c['shared']=='SERIAL_CONFLICT',
  'unknown_serial': c['unknown']=='SERIAL_UNKNOWN',
  'omitted_dependency_false_admission': a['omitted_dependency_exposes_false_admission'],
  'surface_alias_conservative': a['surface_alias_is_conservative'],
  'outcome_agreement': a['independent'] and a['shared'],
  'decision_pass': r['decision']=='PASS_RESOURCE_FOOTPRINT_XTERM_TRANSFER_SCOPED'
}
out={'checks':checks,'pass':all(checks.values())}
print(json.dumps(out,indent=2,sort_keys=True))
raise SystemExit(0 if out['pass'] else 1)
