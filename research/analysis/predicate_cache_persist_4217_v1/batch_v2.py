import json, subprocess, sys, pathlib, copy
ROOT=pathlib.Path(__file__).parent; EXP=ROOT/'experiment.py'; CASES=json.loads((ROOT/'cases.json').read_text())
POLICIES=['VALUE_ONLY_PERSIST','DEPENDENCY_BOUND_PERSIST']

def call(req):
 p=subprocess.run([sys.executable,'-S','-B',str(EXP)],input=json.dumps(req)+'\n',text=True,capture_output=True)
 if p.returncode!=0: raise RuntimeError({'returncode':p.returncode,'stderr':p.stderr})
 return json.loads(p.stdout),p

def main():
 if len(sys.argv)!=3 or sys.argv[1] not in {'construction','formal'} or sys.argv[2] not in {'0','1','2'}: raise SystemExit(2)
 mode=sys.argv[1]; rep=int(sys.argv[2]); selected=CASES if mode=='formal' else CASES[:2]
 path=ROOT/(f'BATCH_V2_REP{rep}.json' if mode=='formal' else f'CONSTRUCTION_V2_REP{rep}.json')
 if path.exists(): raise SystemExit('OUTPUT_EXISTS_REFUSE_OVERWRITE')
 rows=[]
 for c in selected:
  artifact,p=call({'op':'prepare','state':c['before']})
  for policy in POLICIES:
   out,q=call({'op':'consume','policy':policy,'artifact':artifact,'state':c['after']})
   rows.append({'rep':rep,'case':c['name'],'policy':policy,'before':c['before'],'after':c['after'],'artifact':artifact,'result':out,'prepare_exit':p.returncode,'prepare_stderr':p.stderr,'consume_exit':q.returncode,'consume_stderr':q.stderr})
 controls=[]
 if mode=='formal' and rep==2:
  base,_=call({'op':'prepare','state':CASES[0]['before']})
  for name,mut in [('BOOL_VERSION',lambda a:a['key'].__setitem__('intent_version',True)),('BAD_DIGEST',lambda a:a.__setitem__('digest','0'*64)),('MISSING_KEY',lambda a:a.pop('key')),('WRONG_SCHEMA',lambda a:a.__setitem__('schema','bad'))]:
   a=copy.deepcopy(base); mut(a); out,q=call({'op':'consume','policy':'DEPENDENCY_BOUND_PERSIST','artifact':a,'state':CASES[0]['after']})
   controls.append({'name':name,'artifact':a,'state':CASES[0]['after'],'result':out,'exit':q.returncode,'stderr':q.stderr})
 data={'schema':'predicate-persist-batch-v2','mode':mode,'rep':rep,'rows':rows,'controls':controls,'complete':True}
 path.write_text(json.dumps(data,sort_keys=True,indent=2)+'\n')
 print(json.dumps({'path':str(path),'rows':len(rows),'controls':len(controls),'complete':True},sort_keys=True))
if __name__=='__main__': main()
