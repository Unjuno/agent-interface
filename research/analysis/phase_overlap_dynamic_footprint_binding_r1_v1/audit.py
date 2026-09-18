import json,pathlib
r=json.loads((pathlib.Path(__file__).parent/'RESULT.json').read_text()); c=r['counts']
checks={
 'case_count': c['cases']==1152,
 'bound_mismatch_zero': c['bound_mismatch']==0,
 'static_mismatch_zero': c['static_mismatch']==0,
 'unknown_fail_closed': c['unknown_admitted']==0,
 'bound_strict_gain': c['bound_extra_over_static']>0,
 'bound_extra_all_safe': c['bound_extra_safe']==c['bound_extra_over_static'] and c['bound_extra_mismatch']==0,
 'unbound_counterexample': c['unbound_mismatch']>0,
 'selector_write_never_bound_admitted': c['bound_selector_write_admitted']==0,
 'decision': r['decision']=='PASS_DYNAMIC_FOOTPRINT_BINDING_SERIALIZABILITY_SCOPED',
}
o={'checks':checks,'pass':all(checks.values())}; print(json.dumps(o,indent=2,sort_keys=True)); raise SystemExit(0 if o['pass'] else 1)
