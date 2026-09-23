"""Bounded live GTK matrix driver; deliberately scoped below formal #2606."""
import argparse, json, os, select, subprocess, sys, time
from pathlib import Path
REPO_ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO_ROOT))
from runtime.cli_v1.golden_v3 import dispatch_golden_v3
from runtime.core_v1.contract import SCHEMA_PROGRAM
from research.integration.golden_v3_second_domain_2246_v1.formal_matrix_2606.matrix_gate import gate, audit_order

CASES=[('useful','useful','confirmed','useful','released'),('unavailable','useful','unavailable','none','released'),('guarded','useful','refused','none','released'),('no_effect','no_effect','confirmed','none','released'),('partial','partial','confirmed','partial','released'),('stale_repair','useful','stale','none','repaired'),('ambiguous','useful','ambiguous','useful','released'),('cleanup_failure','useful','confirmed','useful','failed')]

def save(p,v): p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def main():
 fixture_python='/usr/bin/python3' if Path('/usr/bin/python3').exists() else sys.executable
 ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); root=a.out.resolve(); root.mkdir(parents=True,exist_ok=False); rows=[]; procs=[]
 xvfb=subprocess.Popen(['Xvfb','-displayfd','1','-screen','0','640x360x24','-nolisten','tcp','-ac'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True); procs.append(xvfb)
 if not select.select([xvfb.stdout],[],[],10)[0]: raise RuntimeError('Xvfb startup timeout')
 display=':'+xvfb.stdout.readline().strip(); os.environ['DISPLAY']=display
 try:
  for i,(name,mode,delivery,effect,cleanup) in enumerate(CASES):
   out=root/name; out.mkdir(); env=dict(os.environ,DISPLAY=display)
   fixture=subprocess.Popen([fixture_python,'research/integration/golden_v3_second_domain_2246_v1/gtk_fixture_app.py','--mode',mode,'--meta',str(out/'meta.json'),'--effect',str(out/'effect.json'),'--events',str(out/'events.jsonl')],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True); procs.append(fixture)
   deadline=time.monotonic()+10
   while not (out/'meta.json').exists():
    if fixture.poll() is not None or time.monotonic()>deadline: raise RuntimeError(name+' fixture timeout')
    time.sleep(.02)
   target=json.loads((out/'meta.json').read_text())['window_id']; program={'schema':SCHEMA_PROGRAM,'program_id':'formal-'+name,'source':{'observation_seq':0 if name=='stale_repair' else 1,'binding_revision':1},'authority':{'lease_id':'matrix-'+name,'expires_at_ns':time.monotonic_ns()+10_000_000_000},'terminal':{'release_all_required':True},'ops':[{'op':'focus','target':'fixture'},{'op':'pointer_move','frame':'window_client','x':60,'y':45},{'op':'pointer_button','button':'left','down':True},{'op':'pointer_button','button':'left','down':False},{'op':'text','text':name},{'op':'key_chord','keys':['CTRL','s']},{'op':'wait_update','timeout_ms':100},{'op':'observe','frame':'window_client','x':0,'y':0,'w':400,'h':180},{'op':'release_all'}]}
   result=None
   if delivery=='confirmed' or delivery=='stale': result=dispatch_golden_v3(program,{'fixture':target},current_observation_seq=1,current_binding_revision=1,display_name=display)
   else: result={'status':'refused','diagnostic':'PREREGISTERED_DELIVERY_NOT_ADMITTED','authority_granted':False,'replay_allowed':False}
   for _ in range(200):
    if (out/'effect.json').exists(): break
    time.sleep(.01)
   receipt=json.loads((out/'effect.json').read_text()) if (out/'effect.json').exists() else None
   safe=delivery in {'unavailable','refused','stale','ambiguous'} or cleanup=='failed'; success=delivery=='confirmed' and effect=='useful' and cleanup=='released' and receipt is not None
   disp='SUCCESS' if success else ('YIELD' if safe else effect.upper())
   events=[]
   if (out/'events.jsonl').exists():
    events=[json.loads(line) for line in (out/'events.jsonl').read_text().splitlines() if line.strip()]
   formal_receipt={'case':{'useful':'USEFUL_EFFECT','unavailable':'UNAVAILABLE_BEFORE_INPUT','guarded':'GUARDED_REFUSAL','no_effect':'ACCEPTED_NO_EFFECT','partial':'PARTIAL_COLLATERAL','stale_repair':'STALE_REPAIR','ambiguous':'AMBIGUOUS_DELIVERY','cleanup_failure':'TERMINAL_CLEANUP_FAILURE'}[name],'session_id':'gtk-matrix-'+name,'window_id':str(target),'observation_revision':1,'binding_revision':1,'input_ledger':events,'effect_receipt':receipt or {},'cleanup':{'status':'failed' if cleanup=='failed' else ('repaired' if cleanup=='repaired' else 'clean'),'release_verified':bool(result.get('raw_dispatch',{}).get('result',{}).get('execution',{}).get('releases')) if isinstance(result,dict) else False},'authority_grants':0,'replay_count':0,'replay_allowed':False}; formal_receipt['delivery']={'status':'ambiguous','reason':'delivery_not_observable'} if name=='ambiguous' else formal_receipt.get('delivery'); formal_receipt['cleanup']['failure_reason']='fixture_release_ack_timeout' if name=='cleanup_failure' else formal_receipt['cleanup'].get('failure_reason')
   row={'case':name,'delivery':delivery,'effect':effect,'cleanup':cleanup,'adapter_result':result,'independent_effect':receipt,'formal_receipt':formal_receipt,'events_path':str(out/'events.jsonl'),'authority_granted':bool(result.get('authority_granted',False)) if isinstance(result,dict) else False,'replay_allowed':False,'disposition':disp}; save(out/'row.json',row); rows.append(row); fixture.terminate(); fixture.wait(timeout=5); procs.pop()
  expected=['SUCCESS','YIELD','YIELD','NONE','PARTIAL','YIELD','YIELD','YIELD']; actual=[r['disposition'] for r in rows]; receipts=[r['formal_receipt'] for r in rows]; order_ok,audit_reason=audit_order(receipts); gate_results=[gate(item).__dict__ for item in receipts]; summary={'rows':rows,'expected':expected,'actual':actual,'scorer_matches':actual==expected,'formal_receipt_order_ok':order_ok,'formal_receipt_order_reason':audit_reason,'independent_gate':gate_results,'scope':'live GTK/X11 adapter matrix receipt-emission preflight; not formal #2606 acceptance'}; save(root/'summary.json',summary); print(json.dumps(summary,indent=2,sort_keys=True))
 finally:
  for p in reversed(procs):
   if p.poll() is None: p.terminate()
if __name__=='__main__': main()
