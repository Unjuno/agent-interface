import json, pathlib, subprocess, sys
root=pathlib.Path(__file__).resolve().parent; plan=json.loads((root/'plan.json').read_text()); out=pathlib.Path(sys.argv[1]); out.mkdir(parents=True,exist_ok=False); rows=[]
for cid,arm in plan['formal_cases']:
    case=out/cid
    p=subprocess.run(['python3',str(root/'run_case.py'),'--arm',arm,'--case-id',cid,'--out',str(case)],capture_output=True,text=True,timeout=8)
    if p.returncode != 0: raise RuntimeError(f'{cid} rc={p.returncode} stderr={p.stderr}')
    rows.append(json.loads((case/'result.json').read_text()))
agg={'task':plan['task'],'formal_invocations':1,'formal_reruns':0,'rows':rows}
(out/'aggregate.json').write_text(json.dumps(agg,indent=2,sort_keys=True)+'\n')
print(json.dumps({'rows':len(rows),'formal_reruns':0},sort_keys=True))
