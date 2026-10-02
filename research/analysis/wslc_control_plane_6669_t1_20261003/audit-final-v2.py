import json,sys,datetime
from pathlib import Path
def load(p): return [json.loads(x) for x in Path(p).read_text(encoding='utf-8-sig').splitlines() if x.strip()]
def check(pressure_path,control_path):
 p=load(pressure_path); c=load(control_path)
 def need(ok,msg):
  if not ok: raise AssertionError(msg)
 ready=[r for r in p if r.get('event')=='pressure_ready' and r.get('allocated_mib')==640]
 need(len(ready)==1,'false success or wrong pressure target')
 av=[]
 for r in p:
  try: av.append(int(r['meminfo']['MemAvailable'].split()[0]))
  except Exception: pass
 need(av and min(av)<128*1024,'pressure threshold not reached')
 labels=[r['label'] for r in c]
 required=['session-info','sessions','list-before','stats','logs-before-stop','stop','list-after-stop','inspect','logs-after-stop','remove','list-after-remove']
 need(all(labels.count(k)==1 for k in required),'missing/duplicate control operation')
 need(all(r['exit']==0 and 0<=r['elapsed_ms']<=15000 for r in c),'control command failed or exceeded deadline')
 by={r['label']:r for r in c}
 need('State":"running' in by['list-before']['output'],'candidate not independently observed running')
 need('MemUsage' in by['stats']['output'],'stats sample missing')
 need('pressure_ready' in by['logs-before-stop']['output'],'raw pressure log missing')
 need('sigterm_received' in by['logs-after-stop']['output'],'candidate did not acknowledge SIGTERM')
 need('signal": 15' in by['logs-after-stop']['output'],'wrong/missing signal number')
 need('Exited (0)' in by['list-after-stop']['output'],'stop did not produce clean exit')
 need(by['list-after-remove']['output'].strip()=='','cleanup absence not independently verified')
 ts=lambda s:datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
 rt=ts(ready[0]['ts']); first=ts(c[0]['ts'])
 overlap=(first-rt).total_seconds()
 need(0<=overlap<=60,'control operations were outside pressure hold')
 return {'audit':'PASS','minimum_memavailable_kib':min(av),'control_ops':len(c),'stop_ms':by['stop']['elapsed_ms'],'pressure_overlap_s':overlap}
if __name__=='__main__':
 try: print(json.dumps(check(sys.argv[1],sys.argv[2])))
 except Exception as e: print(json.dumps({'audit':'REJECT','reason':str(e)})); sys.exit(1)
