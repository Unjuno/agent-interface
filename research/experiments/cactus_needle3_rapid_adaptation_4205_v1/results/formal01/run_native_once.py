import json,pathlib,subprocess,time
s=json.loads(pathlib.Path('/bench/CASES.json').read_text()); out=pathlib.Path('/outputs')
assert len(s['cases'])==7 and not (out/'native-results.jsonl').exists()
rows=[]
with (out/'native-results.jsonl').open('x') as f:
 for i,c in enumerate(s['cases']):
  q='Task: '+c['task']+'\nCurrent visible simulator state (JSON): '+json.dumps(c['state'],sort_keys=True,separators=(',',':'))+'\nPolicy: '+s['policy']+'\nChoose exactly one next tool action, or explicitly yield / take no action when appropriate. Use the exact current scope_id and generation from current state. Do not infer missing facts.'
  t=time.perf_counter_ns(); p=subprocess.run(['/opt/needle/needle','--model','/assets/candidate.cact','--tools','/assets/tools.json','--system','device: isolated desktop-settings simulator; network: disabled','--prompt',q,'--threads','2','--max','128'],capture_output=True,text=True,check=True); ms=(time.perf_counter_ns()-t)/1e6
  r=json.loads(p.stdout); calls=r.get('function_calls',[]); exact=calls==c['expected']; rec={'index':i,'id':c['id'],'expected':c['expected'],'expected_effect':c['expected_effect'],'response':r,'latency_ms':ms,'exact':exact}
  f.write(json.dumps(rec,separators=(',',':'),allow_nan=False)+'\n');f.flush();rows.append(rec);print(i+1,c['id'],exact,round(ms,2),flush=True)
lat=sorted(x['latency_ms'] for x in rows); print(json.dumps({'schema':'candidate-eval-v1','count':len(rows),'exact':sum(x['exact'] for x in rows),'warm_p95_ms':lat[6],'formal_invocations':1,'reruns':0,'tuning':0},sort_keys=True))