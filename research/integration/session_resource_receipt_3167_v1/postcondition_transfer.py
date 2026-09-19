import json,os,subprocess,tempfile,time,sys
from pathlib import Path
sys.path.insert(0,'/workspace')
from runtime.cli_v1.golden_v3 import dispatch_golden_v3
display=':154';env=os.environ.copy();env['DISPLAY']=display;os.environ['DISPLAY']=display
root=Path(tempfile.mkdtemp(prefix='receipt-post-'));ps=[]
try:
 xv=subprocess.Popen(['Xvfb',display,'-screen','0','800x400x24','-nolisten','tcp','-ac'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);ps.append(xv);time.sleep(.5)
 def start(n,mode):
  d=root/n;d.mkdir();p=subprocess.Popen(['/usr/bin/python3','/workspace/research/integration/golden_v3_second_domain_2246_v1/gtk_fixture_app.py','--mode',mode,'--meta',str(d/'meta.json'),'--effect',str(d/'effect.json')],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);ps.append(p);end=time.monotonic()+10
  while not(d/'meta.json').exists() and time.monotonic()<end:time.sleep(.02)
  return p,d,str(json.loads((d/'meta.json').read_text())['window_id'])
 p1,d1,x1=start('useful','useful');p2,d2,x2=start('no_effect','no_effect')
 def receipt(session,x):return {'session_id':session,'resource_id':x,'generation':1,'source_digest':str(x)}
 def dispatch(x):
  prog={'schema':'agent-interface/program-v1','program_id':'postcondition','source':{'observation_seq':1,'binding_revision':1},'authority':{'lease_id':'p','expires_at_ns':time.monotonic_ns()+5_000_000_000},'terminal':{'release_all_required':True},'ops':[{'op':'focus','target':'fixture'},{'op':'key_chord','keys':['CTRL','s']},{'op':'release_all'}]}
  return dispatch_golden_v3(prog,{'fixture':int(x)},current_observation_seq=1,current_binding_revision=1,display_name=display)
 rows=[]
 for n,d,x in [('useful',d1,x1),('no_effect',d2,x2)]:
  r=receipt('s-'+n,x);out=dispatch(x);time.sleep(.15);effect=(d/'effect.json').exists(); rows.append({'case':n,'receipt_bound':True,'native_status':out.get('native_status'),'emissions':out.get('raw_dispatch',{}).get('result',{}).get('execution',{}).get('program_emissions',0),'transport_completed':out.get('native_status')=='completed','effect_present':effect,'disposition':'SUCCESS' if effect else 'ACCEPTED_NO_EFFECT'})
 print(json.dumps({'decision':'PASS_TRANSPORT_POSTCONDITION_SEPARATION_SCOPED' if rows[0]['effect_present'] and not rows[1]['effect_present'] and rows[1]['disposition']=='ACCEPTED_NO_EFFECT' else 'FAIL_FALSE_TASK_SUCCESS','rows':rows,'model_calls':0,'network_calls':0},sort_keys=True))
finally:
 for p in reversed(ps):
  if p.poll() is None:p.terminate()
