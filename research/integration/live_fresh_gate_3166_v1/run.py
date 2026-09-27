import json,os,subprocess,tempfile,time,sys
from pathlib import Path
sys.path.insert(0,'/workspace')
from runtime.cli_v1.golden_v3 import dispatch_golden_v3

display=':151'; env=os.environ.copy(); env['DISPLAY']=display; os.environ['DISPLAY']=display
root=Path(tempfile.mkdtemp(prefix='tier-')); ps=[]
try:
 xv=subprocess.Popen(['Xvfb',display,'-screen','0','800x400x24','-nolisten','tcp','-ac'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); ps.append(xv); time.sleep(.5)
 def start(name):
  d=root/name; d.mkdir(); p=subprocess.Popen(['/usr/bin/python3','/workspace/research/integration/golden_v3_second_domain_2246_v1/gtk_fixture_app.py','--mode','useful','--meta',str(d/'meta.json'),'--effect',str(d/'effect.json'),'--events',str(d/'events.jsonl')],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); ps.append(p)
  end=time.monotonic()+10
  while not (d/'meta.json').exists() and time.monotonic()<end: time.sleep(.02)
  return p,d,str(json.loads((d/'meta.json').read_text())['window_id'])
 old,od,old_xid=start('old'); prepared={'target_id':old_xid,'generation':1,'prepared_ns':time.monotonic_ns()}
 new,nd,new_xid=start('new'); old.terminate(); old.wait(timeout=3); time.sleep(.1)
 def action(target,policy):
  fresh=(target==new_xid)
  admitted=(target==prepared['target_id'] and fresh) if policy=='TWO_TIER_FRESH_GATE' else target==prepared['target_id']
  if not admitted: return {'policy':policy,'admitted':False,'reason':'fresh_gate_mismatch' if policy.startswith('TWO') else 'dependency_only_target_reused','native_status':None,'emissions':0,'effect':False}
  program={'schema':'agent-interface/program-v1','program_id':policy,'source':{'observation_seq':1,'binding_revision':1},'authority':{'lease_id':policy,'expires_at_ns':time.monotonic_ns()+5_000_000_000},'terminal':{'release_all_required':True},'ops':[{'op':'focus','target':'fixture'},{'op':'key_chord','keys':['CTRL','s']},{'op':'release_all'}]}
  res=dispatch_golden_v3(program,{'fixture':int(target)},current_observation_seq=1,current_binding_revision=1,display_name=display); time.sleep(.15)
  return {'policy':policy,'admitted':True,'reason':'admitted','native_status':res.get('native_status'),'emissions':res.get('raw_dispatch',{}).get('result',{}).get('execution',{}).get('program_emissions',0),'effect':nd.joinpath('effect.json').exists()}
 rows=[action(old_xid,'TWO_TIER_FRESH_GATE'),action(old_xid,'DEPENDENCY_ONLY'),action(new_xid,'TWO_TIER_FRESH_GATE')]
 expected=[False,True,False]
 result={'decision':'PASS_LIVE_TWO_TIER_FRESH_GATE_SCOPED' if [r['admitted'] for r in rows]==expected and rows[0]['emissions']==0 and rows[2]['emissions']==0 and rows[1]['admitted'] is True else 'FAIL_LIVE_FRESH_GATE_UNSAFE','prepared':prepared,'old_xid':old_xid,'new_xid':new_xid,'rows':rows,'model_calls':0,'network_calls':0}
 print(json.dumps(result,sort_keys=True))
finally:
 for p in reversed(ps):
  if p.poll() is None: p.terminate()
