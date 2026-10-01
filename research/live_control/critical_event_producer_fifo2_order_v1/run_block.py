import argparse,json,pathlib,subprocess,sys
p=argparse.ArgumentParser(); p.add_argument('--plan',required=True); p.add_argument('--out',required=True); a=p.parse_args()
plan=json.loads(pathlib.Path(a.plan).read_text()); out=pathlib.Path(a.out); out.mkdir(parents=True,exist_ok=False); rows=[]
root=pathlib.Path(__file__).parent
for case in plan['cases']:
    cdir=out/case['id']; cp=subprocess.run([sys.executable,str(root/'run_case.py'),'--arm',case['arm'],'--case-id',case['id'],'--out',str(cdir)],cwd=root,capture_output=True,text=True,check=False)
    if cp.returncode!=0: raise RuntimeError(f"{case['id']} rc={cp.returncode} stderr={cp.stderr}")
    r=json.loads((cdir/'result.json').read_text()); r['runner_stdout']=cp.stdout; r['runner_stderr']=cp.stderr; rows.append(r)
agg={'task':plan['task'],'base':plan['base'],'formal_allocation':plan['formal_allocation'],'rows':rows,'formal_reruns':0}
(out/'aggregate.json').write_text(json.dumps(agg,sort_keys=True,indent=2)+'\n'); print(json.dumps({'rows':len(rows),'out':str(out)},sort_keys=True))
