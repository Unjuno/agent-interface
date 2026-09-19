from __future__ import annotations
import argparse,hashlib,json,random
from pathlib import Path
from policy import authority_guarded,handoff_fenced

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def p(pid,source,gen,at=11,resource='locomotion',authority_id=None):return {'proposal_id':pid,'resource':resource,'source':source,'generation':gen,'authority_id':authority_id,'proposed_at':at,'ready':True}
def lease(**kw):
 d={'authority_id':'T1','resource':'locomotion','generation':1,'active':True,'valid_context':True,'start_tick':0,'end_tick':20};d.update(kw);return d

def fixture(name):
 if name=='expired_old_deopt':return [p('d-old','deopt',1)],[lease()],{'locomotion':2},21
 if name=='expired_fresh_deopt':return [p('d-fresh','deopt',2,21)],[lease()],{'locomotion':2},21
 if name=='expired_old_threat':return [p('t-old','threat',1,11,authority_id='T1')],[lease()],{'locomotion':2},21
 if name=='expired_fresh_unowned_threat':return [p('t-fresh','threat',2,21,authority_id='T1')],[lease()],{'locomotion':2},21
 if name=='invalidated_old_deopt':return [p('d-old','deopt',1)],[lease(valid_context=False)],{'locomotion':2},12
 if name=='no_authority_deopt':return [p('d','deopt',1)],[],{'locomotion':1},12
 if name=='nonoverlap_resources':return [p('t','threat',1,10,'fire','T1'),p('d','deopt',1,11,'locomotion')],[lease(resource='fire')],{'fire':1,'locomotion':1},12
 if name=='active_overlap':return [p('t','threat',1,10,authority_id='T1'),p('d','deopt',1,11)],[lease()],{'locomotion':1},12
 raise KeyError(name)

def expected(name):
 base={
  'expired_old_deopt':{'locomotion':'deopt'},'expired_fresh_deopt':{'locomotion':'deopt'},'expired_old_threat':{'locomotion':'threat'},'expired_fresh_unowned_threat':{'locomotion':'threat'},'invalidated_old_deopt':{'locomotion':'deopt'},'no_authority_deopt':{'locomotion':'deopt'},'nonoverlap_resources':{'fire':'threat','locomotion':'deopt'},'active_overlap':{'locomotion':'threat'}}
 cand={
  'expired_old_deopt':{},'expired_fresh_deopt':{'locomotion':'deopt'},'expired_old_threat':{},'expired_fresh_unowned_threat':{},'invalidated_old_deopt':{},'no_authority_deopt':{'locomotion':'deopt'},'nonoverlap_resources':{'fire':'threat','locomotion':'deopt'},'active_overlap':{'locomotion':'threat'}}
 return {'authority_guarded':base[name],'handoff_fenced':cand[name]}

def simple(out):return {r:v['source'] for r,v in sorted(out['selected'].items())}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--plan',required=True);ap.add_argument('--out',required=True);a=ap.parse_args();planp=Path(a.plan);plan=json.loads(planp.read_text());out=Path(a.out)
 if out.exists():raise SystemExit('refuse existing output')
 sched=[(rep,s) for rep in range(plan['repetitions']) for s in plan['scenarios']];random.Random(plan['seed']).shuffle(sched);rows=[]
 for i,(rep,scenario) in enumerate(sched):
  props,leases,gens,tick=fixture(scenario);ex=expected(scenario)
  for name,fn in [('authority_guarded',authority_guarded),('handoff_fenced',handoff_fenced)]:
   o=fn(props,leases,gens,tick);sel=simple(o);rows.append({'row_id':f'm{i:02d}-{name}','schedule_index':i,'rep':rep,'scenario':scenario,'policy':name,'tick':tick,'generations':gens,'proposals':props,'leases':leases,'selected':sel,'deferred':o['deferred'],'expected':ex[name],'correct':sel==ex[name]})
 data={'schema':'agent-interface/map01-threat-deopt-handoff-fence-result-v1','task':plan['task'],'plan_sha256':sha(planp),'rows':rows};out.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n');print(json.dumps({'rows':len(rows),'correct':sum(r['correct'] for r in rows)},sort_keys=True))
if __name__=='__main__':main()
