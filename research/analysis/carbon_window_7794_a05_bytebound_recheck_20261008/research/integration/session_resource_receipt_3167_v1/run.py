import hashlib,json,os,subprocess,tempfile,time,sys
from pathlib import Path
from Xlib import display
display_name=':152'; env=os.environ.copy(); env['DISPLAY']=display_name; os.environ['DISPLAY']=display_name
def validate(r,current,used):
    if not isinstance(r,dict): return False,'malformed'
    if r.get('receipt_id') in used: return False,'duplicate'
    for k in ('session_id','resource_id','generation','source_digest'):
        if r.get(k)!=current.get(k): return False,'binding_mismatch'
    return True,'bound'
root=Path(tempfile.mkdtemp(prefix='receipt-')); ps=[]
try:
 xv=subprocess.Popen(['Xvfb',display_name,'-screen','0','800x400x24','-nolisten','tcp','-ac'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); ps.append(xv); time.sleep(.5)
 def start(name):
  d=root/name; d.mkdir(); p=subprocess.Popen(['/usr/bin/python3','/workspace/research/integration/golden_v3_second_domain_2246_v1/gtk_fixture_app.py','--mode','useful','--meta',str(d/'meta.json'),'--effect',str(d/'effect.json')],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); ps.append(p)
  end=time.monotonic()+10
  while not (d/'meta.json').exists() and time.monotonic()<end: time.sleep(.02)
  return p,d,str(json.loads((d/'meta.json').read_text())['window_id'])
 old,od,xid1=start('resource1'); src1=hashlib.sha256((od/'meta.json').read_bytes()).hexdigest(); current={'session_id':'s1','resource_id':xid1,'generation':1,'source_digest':src1}; base=dict(current,receipt_id='r1')
 new,nd,xid2=start('resource2'); src2=hashlib.sha256((nd/'meta.json').read_bytes()).hexdigest()
 cases=[('same_session_resource',base,current,[]),('session_restart',base,dict(current,session_id='s2'),[]),('resource_replacement',base,dict(current,resource_id=xid2),[]),('generation_change',base,dict(current,generation=2),[]),('source_change',base,dict(current,source_digest=src2),[]),('cross_session',base,dict(current,session_id='s2'),[]),('malformed',None,current,[]),('duplicate',base,current,['r1'])]
 rows=[]
 for name,r,c,u in cases:
  ok,reason=validate(r,c,u); rows.append({'case':name,'admitted':ok,'reason':reason})
 expected={'same_session_resource':True,'session_restart':False,'resource_replacement':False,'generation_change':False,'source_change':False,'cross_session':False,'malformed':False,'duplicate':False}
 result={'decision':'PASS_SESSION_RESOURCE_RECEIPT_BRIDGE_SCOPED' if all(x['admitted']==expected[x['case']] for x in rows) and xid1!=xid2 else 'FAIL_RECEIPT_BOUNDARY_UNSAFE','xid1':xid1,'xid2':xid2,'source1':src1,'source2':src2,'rows':rows,'model_calls':0,'network_calls':0}
 print(json.dumps(result,sort_keys=True))
finally:
 for p in reversed(ps):
  if p.poll() is None:p.terminate()
