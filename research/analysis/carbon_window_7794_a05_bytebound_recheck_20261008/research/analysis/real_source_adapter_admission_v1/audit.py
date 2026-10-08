import json,pathlib
root=pathlib.Path(__file__).parent
r=json.loads((root/'RESULT.json').read_text());s=r['stats'];p=r['pinned']
checks={
 'focus_blob':p['focus_formal_summary_blob']=='8557cc1a70487df7abbfffb965a9e4d38ac3bfd5',
 'chromium_fixture_blob':p['chromium_fixture_blob']=='349b4e19d88d718f159dabc362136f5a02b1ed89',
 'chromium_report_blob':p['chromium_report_blob']=='ee13e4abe3f77f2234bc69e1a948170a979523c5',
 'rows_7':r['rows']==7,
 'focus_admissible':s['focus_generation_identity']['evidence_complete']=='ADMISSIBLE',
 'focus_exact':s['focus_generation_identity']['false_accepts']==0 and s['focus_generation_identity']['false_rejects']==0,
 'chromium_incomplete':s['chromium_coarse_context']['evidence_complete']=='INCOMPLETE',
 'chromium_false_accept':s['chromium_coarse_context']['false_accepts']>0,
 'name_only_false_complete':r['name_only_false_complete']>0,
 'decision_pass':r['decision']=='PASS_REAL_SOURCE_ADAPTER_ADMISSION_SCOPED'
}
out={'checks':checks,'pass':all(checks.values())}
print(json.dumps(out,indent=2,sort_keys=True))
raise SystemExit(0 if out['pass'] else 1)
