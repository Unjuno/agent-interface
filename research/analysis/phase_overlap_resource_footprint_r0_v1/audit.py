import json, pathlib
root=pathlib.Path(__file__).parent
r=json.loads((root/'RESULT.json').read_text())
c=r['counts']
checks={
 'complete_footprint_mismatch_zero': c['complete_mismatch']==0,
 'complete_overlap_nonvacuous': c['complete_admitted']>0,
 'all_declared_conflicts_serialized': c['declared_conflicts_serialized']==c['declared_conflicts_total'],
 'unknown_fail_closed': c['unknown_parallel_admissions']==0,
 'surface_only_discriminator': c['surface_only_mismatches']>0,
 'omitted_dependency_discriminator': c['omitted_dependency_mismatches']>0,
 'reverse_predicate_discriminator': c['reverse_predicate_mismatches']>0,
 'both_orders_exercised': c['both_serial_orders_exercised']==2,
 'decision_pass': r['decision']=='PASS_PHASE_OVERLAP_RESOURCE_FOOTPRINT_SERIALIZABILITY_SCOPED',
 'expected_case_count': c['cases']==186624,
}
out={'checks':checks,'pass':all(checks.values())}
print(json.dumps(out,indent=2,sort_keys=True))
raise SystemExit(0 if out['pass'] else 1)
