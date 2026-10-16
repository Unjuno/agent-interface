import argparse,json,pathlib
p=argparse.ArgumentParser(); p.add_argument('--plan',required=True); p.add_argument('--root',required=True); p.add_argument('--out',required=True); a=p.parse_args()
plan=json.loads(pathlib.Path(a.plan).read_text()); root=pathlib.Path(a.root); rows=[]
for case in plan['cases']:
    f=root/case['id']/'result.json'
    if not f.exists(): raise SystemExit(f'missing first outcome {case["id"]}')
    r=json.loads(f.read_text())
    if r['case_id']!=case['id'] or r['policy']!=case['policy'] or r['arrival']!=case['arrival']: raise SystemExit(f'case mismatch {case["id"]}')
    rows.append(r)
agg={'task':plan['task'],'base':plan['base'],'formal_allocation':plan['formal_allocation'],'rows':rows,'formal_reruns':0,'a1_rows_pooled':0,'supervision_change_only':True}
pathlib.Path(a.out).write_text(json.dumps(agg,sort_keys=True,indent=2)+'\n')
print(json.dumps({'rows':len(rows),'allocation':plan['formal_allocation']},sort_keys=True))
