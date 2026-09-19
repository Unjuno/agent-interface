import json, subprocess, sys, pathlib
root=pathlib.Path(__file__).parent
expected=json.loads((root/'RESULT.json').read_text())
actual=json.loads(subprocess.check_output([sys.executable,str(root/'analyze.py')],text=True))
checks={
    'exact_recompute': actual==expected,
    'lower_bound_violations_zero': actual['lower_bound_violations']==0,
    'aliased_pointer_counterexamples_zero': actual['aliased_pointer_counterexamples']==0,
    'strict_speedup_nonvacuous': actual['strict_speedup_cases_vs_global_serial_baseline']>0,
    'same_pointer_example_no_speedup': next(x for x in actual['examples'] if x['name']=='two_logical_cursors_same_pointer')['speedup']==1.0,
    'independent_pointer_example_speedup': next(x for x in actual['examples'] if x['name']=='two_independent_virtual_pointers')['speedup']>1.0,
    'dependency_can_dominate': next(x for x in actual['examples'] if x['name']=='dependency_dominates')['speedup']==1.0,
}
out={'checks':checks,'pass':all(checks.values())}
print(json.dumps(out,indent=2))
raise SystemExit(0 if out['pass'] else 1)
