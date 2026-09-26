import json,pathlib,sys
R=pathlib.Path(__file__).parent; outp=R/'FORMAL_V2.json'
if outp.exists(): raise SystemExit('FORMAL_V2_EXISTS_REFUSE_OVERWRITE')
rows=[]; controls=[]
for rep in range(3):
 p=R/f'BATCH_V2_REP{rep}.json'
 if not p.exists(): raise SystemExit(f'MISSING_BATCH_{rep}')
 d=json.loads(p.read_text())
 if d.get('schema')!='predicate-persist-batch-v2' or d.get('mode')!='formal' or d.get('rep')!=rep or d.get('complete') is not True or len(d.get('rows',[]))!=16: raise SystemExit(f'INVALID_BATCH_{rep}')
 if rep<2 and d.get('controls')!=[]: raise SystemExit(f'UNEXPECTED_CONTROLS_{rep}')
 if rep==2 and len(d.get('controls',[]))!=4: raise SystemExit('INVALID_CONTROLS_2')
 rows.extend(d['rows']); controls.extend(d['controls'])
out={'schema':'predicate-persist-formal-v1','rows':rows,'controls':controls,'row_count':len(rows),'formal_invocations':1,'allocation':'predicate-cache-persist-4217-20260923-02','batch_count':3}
outp.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
print(json.dumps({'path':str(outp),'rows':len(rows),'controls':len(controls),'batches':3},sort_keys=True))
