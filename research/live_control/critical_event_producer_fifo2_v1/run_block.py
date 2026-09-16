import json, pathlib, subprocess, sys
root=pathlib.Path(__file__).parent; plan=json.loads((root/'plan.json').read_text()); out=pathlib.Path(sys.argv[1]); out.mkdir(parents=True,exist_ok=False); rows=[]
for cid,policy in plan['cases']:
    d=out/cid
    subprocess.run([sys.executable,str(root/'run_case.py'),'--policy',policy,'--id',cid,'--out',str(d)],check=True,capture_output=True,text=True,env={**__import__('os').environ,'PYTHONPATH':str(root)})
    rows.append(json.loads((d/'result.json').read_text()))
agg={'formal_id':plan['formal_id'],'rows':rows,'formal_reruns':0}; (out/'aggregate.json').write_text(json.dumps(agg,sort_keys=True,indent=2)+'\n')
