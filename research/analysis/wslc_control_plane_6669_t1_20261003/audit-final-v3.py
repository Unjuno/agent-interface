import json,sys,datetime
from pathlib import Path
def load(p): return [json.loads(x) for x in Path(p).read_text(encoding='utf-8-sig').splitlines() if x.strip()]
def need(ok,msg):
 if not ok: raise AssertionError(msg)
def audit_pressure(pp,cp):
 p=load(pp); c=load(cp)
 ready=[r for r in p if r.get('event')=='pressure_ready' and r.get('allocated_mib')==640]
 need(len(ready)==1,'false success or wrong pressure target')
 alloc=[r.get('allocated_mib',0) for r in p]
 need(all(isinstance(x,int) and 0<=x<=640 for x in alloc),'allocation exceeded frozen maximum')
 av=[]
 for r in p:
  try: av.append(int(r['meminfo']['MemAvailable'].split()[0]))
  except Exception: pass
 need(av and min(av)<128*1024,'pressure threshold not reached')
 labels=[r['label'] for r in c]
 required=['session-info','sessions','list-before','stats','logs-before-stop','stop','list-after-stop','inspect','logs-after-stop','remove','list-after-remove']
 need(all(labels.count(k)==1 for k in required),'missing/duplicate pressure control operation')
 need(all(r['exit']==0 and 0<=r['elapsed_ms']<=15000 for r in c),'pressure control command failed or exceeded deadline')
 by={r['label']:r for r in c}
 need('State":"running' in by['list-before']['output'],'pressure candidate not observed running')
 need('MemUsage' in by['stats']['output'],'pressure stats sample missing')
 need('pressure_ready' in by['logs-before-stop']['output'],'raw pressure log missing')
 need('sigterm_received' in by['logs-after-stop']['output'] and 'signal": 15' in by['logs-after-stop']['output'],'SIGTERM not acknowledged')
 need('Exited (0)' in by['list-after-stop']['output'],'pressure stop did not produce clean exit')
 need(by['list-after-remove']['output'].strip()=='','pressure cleanup not independently verified')
 ts=lambda s:datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
 rt=ts(ready[0]['ts']); first=ts(by['session-info']['ts']); last=ts(next(r for r in p if r.get('event')=='sigterm_received')['ts'])
 overlap=(first-rt).total_seconds()
 need(0<=overlap<=60 and (last-rt).total_seconds()<=60,'control operations outside pressure hold')
 return {'minimum_memavailable_kib':min(av),'control_ops':len(c),'stop_ms':by['stop']['elapsed_ms'],'pressure_overlap_s':overlap}
def audit_control(pp,cp):
 p=load(pp);c=load(cp)
 need(any(r.get('event')=='baseline_ready' and r.get('allocated_mib')==32 for r in p),'matched baseline missing')
 av=[int(r['meminfo']['MemAvailable'].split()[0]) for r in p if 'MemAvailable' in r.get('meminfo',{})]
 need(av and min(av)>128*1024,'matched control unexpectedly pressured')
 need(any(r.get('event')=='sigterm_received' and r.get('signal')==15 for r in p),'matched control did not acknowledge SIGTERM')
 by={r['label']:r for r in c}
 need(all(k in by for k in ('stop','list-after-stop','logs-after-stop','remove','list-after-remove')),'matched control operations missing')
 need(all(by[k]['exit']==0 and by[k]['elapsed_ms']<=15000 for k in ('stop','list-after-stop','logs-after-stop','remove','list-after-remove')),'matched control operation failed')
 need('Exited (0)' in by['list-after-stop']['output'] and by['list-after-remove']['output'].strip()=='','matched control cleanup/exit failed')
 return {'baseline_stop_ms':by['stop']['elapsed_ms']}
if __name__=='__main__':
 try:
  a=audit_pressure(sys.argv[1],sys.argv[2]);b=audit_control(sys.argv[3],sys.argv[4])
  print(json.dumps({'audit':'PASS',**a,**b}))
 except Exception as e: print(json.dumps({'audit':'REJECT','reason':str(e)}));sys.exit(1)
