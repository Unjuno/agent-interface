import hashlib,json,os,subprocess,tempfile,time,sys
from pathlib import Path
sys.path.insert(0,'/workspace')
from runtime.cli_v1.golden_v3 import dispatch_golden_v3
display=':153'; env=os.environ.copy(); env['DISPLAY']=display; os.environ['DISPLAY']=display
root=Path(tempfile.mkdtemp(prefix='receipt-effect-')); ps=[]
def valid(r,c,used):
 if not isinstance(r,dict) or r.get('receipt_id') in used:return False
 return all(r.get(k)==c.get(k) for k in ('session_id','resource_id','generation','source_digest'))
try:
 xv=subprocess.Popen(['Xvfb',display,'-screen','0','800x400x24','-nolisten','tcp','-ac'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);ps.append(xv);time.sleep(.5)
 def start(n):
  d=root/n;d.mkdir();p=subprocess.Popen(['/usr/bin/python3','/workspace/research/integration/golden_v3_second_domain_2246_v1/gtk_fixture_app.py','--mode','useful','--meta',str(d/'meta.json'),'--effect',str(d/'effect.json')],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);ps.append(p);end=time.monotonic()+10
  while not(d/'meta.json').exists() and time.monotonic()<end:time.sleep(.02)
  return p,d,str(json.loads((d/'meta.json').read_text())['window_id'])
 p1,d1,x1=start('resource1');p2,d2,x2=start('resource2');s1=hashlib.sha256((d1/'meta.json').read_bytes()).hexdigest();s2=hashlib.sha256((d2/'meta.json').read_bytes()).hexdigest();r=dict(receipt_id='r1',session_id='s1',resource_id=x1,generation=1,source_digest=s1)
 def dispatch(x):
  prog={'schema':'agent-interface/program-v1','program_id':'receipt-effect','source':{'observation_seq':1,'binding_revision':1},'authority':{'lease_id':'r1','expires_at_ns':time.monotonic_ns()+5_000_000_000},'terminal':{'release_all_required':True},'ops':[{'op':'focus','target':'fixture'},{'op':'key_chord','keys':['CTRL','s']},{'op':'release_all'}]}
  return dispatch_golden_v3(prog,{'fixture':int(x)},current_observation_seq=1,current_binding_revision=1,display_name=display)
 cases=[('valid',r,dict(session_id='s1',resource_id=x1,generation=1,source_digest=s1),[],x1),('replacement',r,dict(session_id='s1',resource_id=x2,generation=1,source_digest=s2),[],x2),('cross_session',r,dict(session_id='s2',resource_id=x1,generation=1,source_digest=s1),[],x1),('duplicate',r,dict(session_id='s1',resource_id=x1,generation=1,source_digest=s1),['r1'],x1)]
 rows=[]
 for n,rec,cur,used,x in cases:
  admitted=valid(rec,cur,used); out=dispatch(x) if admitted else None; time.sleep(.15); effect=(d1/'effect.json').exists() if n=='valid' else (d2/'effect.json').exists() if n=='replacement' else False
  rows.append({'case':n,'admitted':admitted,'effect':effect,'native_status':out.get('native_status') if out else None,'emissions':out.get('raw_dispatch',{}).get('result',{}).get('execution',{}).get('program_emissions',0) if out else 0})
 ok=rows[0]['admitted'] and rows[0]['effect'] and all(not x['admitted'] and not x['effect'] for x in rows[1:])
 print(json.dumps({'decision':'PASS_SESSION_RESOURCE_EFFECT_TRANSFER_SCOPED' if ok else 'FAIL_RECEIPT_EFFECT_BOUNDARY','xid1':x1,'xid2':x2,'source1':s1,'source2':s2,'rows':rows,'model_calls':0,'network_calls':0},sort_keys=True))
finally:
 for p in reversed(ps):
  if p.poll() is None:p.terminate()
