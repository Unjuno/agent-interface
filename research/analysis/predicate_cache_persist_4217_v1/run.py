import json, subprocess, sys, pathlib, copy
ROOT=pathlib.Path(__file__).parent
EXP=ROOT/'experiment.py'; cases=json.loads((ROOT/'cases.json').read_text())
policies=['VALUE_ONLY_PERSIST','DEPENDENCY_BOUND_PERSIST']
path=ROOT/'FORMAL.json'
if path.exists():
    raise SystemExit('FORMAL_EXISTS_REFUSE_OVERWRITE')
rows=[]
for rep in range(3):
  for c in cases:
    p=subprocess.run([sys.executable,'-B',str(EXP)],input=json.dumps({'op':'prepare','state':c['before']})+'\n',text=True,capture_output=True,check=True)
    artifact=json.loads(p.stdout)
    for policy in policies:
      q=subprocess.run([sys.executable,'-B',str(EXP)],input=json.dumps({'op':'consume','policy':policy,'artifact':artifact,'state':c['after']})+'\n',text=True,capture_output=True,check=True)
      out=json.loads(q.stdout)
      rows.append({'rep':rep,'case':c['name'],'policy':policy,'before':c['before'],'after':c['after'],'artifact':artifact,'result':out,'prepare_exit':p.returncode,'prepare_stderr':p.stderr,'consume_exit':q.returncode,'consume_stderr':q.stderr})
base=json.loads(subprocess.run([sys.executable,'-B',str(EXP)],input=json.dumps({'op':'prepare','state':cases[0]['before']})+'\n',text=True,capture_output=True,check=True).stdout)
controls=[]
for name,mut in [
 ('BOOL_VERSION',lambda a:a['key'].__setitem__('intent_version',True)),
 ('BAD_DIGEST',lambda a:a.__setitem__('digest','0'*64)),
 ('MISSING_KEY',lambda a:a.pop('key')),
 ('WRONG_SCHEMA',lambda a:a.__setitem__('schema','bad')),
]:
 a=copy.deepcopy(base); mut(a)
 q=subprocess.run([sys.executable,'-B',str(EXP)],input=json.dumps({'op':'consume','policy':'DEPENDENCY_BOUND_PERSIST','artifact':a,'state':cases[0]['after']})+'\n',text=True,capture_output=True,check=True)
 controls.append({'name':name,'artifact':a,'state':cases[0]['after'],'result':json.loads(q.stdout),'exit':q.returncode,'stderr':q.stderr})
out={'schema':'predicate-persist-formal-v1','rows':rows,'controls':controls,'row_count':len(rows),'formal_invocations':1}
path.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
print(json.dumps({'rows':len(rows),'controls':len(controls),'path':str(path)}))
