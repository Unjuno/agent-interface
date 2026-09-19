import json,random,hashlib,pathlib
from candidate import Actuation,Effect,clock_bound,numeric_only
from oracle import classify,parent988
A=Actuation('a1',10,14,'mono','boot1')
def E(**kw):
    x=dict(effect_id='e1',actuation_id='a1',t_ns=20,scored=True,useful=True,clock_domain='mono',clock_epoch='boot1');x.update(kw);return Effect(**x)
fixed=[
 (E(t_ns=9),[A]),(E(t_ns=10),[A]),(E(t_ns=13),[A]),(E(t_ns=14),[A]),
 (E(clock_domain='other'),[A]),(E(clock_epoch='boot2'),[A]),(E(clock_domain=None),[A]),
 (E(effect_id=''),[A]),(E(t_ns=-1),[A]),(E(scored=False,clock_domain='other'),[A]),
 (E(actuation_id=None,clock_domain='other'),[A]),(E(actuation_id='unknown',useful=False,clock_domain='other'),[A])]
fp=sum(clock_bound(e,a)==classify(e,a) for e,a in fixed)
# same-clock parent degeneration over boundary regions and usefulness/scored/bound cases
pd=pt=0
for t in [0,9,10,11,13,14,20]:
  for useful in [False,True]:
   for scored in [False,True]:
    for aid in ['a1',None,'unknown']:
      e=E(t_ns=t,useful=useful,scored=scored,actuation_id=aid)
      c=clock_bound(e,[A]); p=parent988(e,[A]); pt+=1; pd+=(c==p)

rng=random.Random(100420260917001); N=425000
mismatch=0; cross_numeric_promoted=0; cross_bound_promoted=0; same_parent_mismatch=0; status={}; h=hashlib.sha256()
doms=['monoA','monoB','']; epochs=['ep1','ep2','']; ids=['a0','a1','a2']
for i in range(N):
    acts=[]
    for j in range(rng.randint(0,3)):
      aid=ids[j]; lo=rng.randint(0,100); hi=lo+rng.randint(0,7); acts.append(Actuation(aid,lo,hi,rng.choice(doms),rng.choice(epochs)))
    aid=rng.choice(ids+[None,'unknown'])
    e=Effect(f'e{i}',aid,rng.randint(-3,115),rng.random()<.82,rng.random()<.5,rng.choice(doms),rng.choice(epochs))
    try:
      c=clock_bound(e,acts); o=classify(e,acts)
      if c!=o:mismatch+=1
      status[c]=status.get(c,0)+1
      # Discriminator only for scored+bound records with complete but mismatched clocks.
      amap={a.actuation_id:a for a in acts}
      if e.scored and e.t_ns>=0 and aid in amap and e.clock_domain and e.clock_epoch and amap[aid].clock_domain and amap[aid].clock_epoch and (e.clock_domain,e.clock_epoch)!=(amap[aid].clock_domain,amap[aid].clock_epoch):
        n=numeric_only(e,acts)
        if n in ('useful_bound','nonuseful_bound'): cross_numeric_promoted+=1
        if c in ('useful_bound','nonuseful_bound'): cross_bound_promoted+=1
      if aid in amap and e.clock_domain and e.clock_epoch and (e.clock_domain,e.clock_epoch)==(amap[aid].clock_domain,amap[aid].clock_epoch):
        same_parent_mismatch += (c!=parent988(e,acts))
      h.update(json.dumps([e.__dict__,[a.__dict__ for a in acts],c],sort_keys=True,separators=(',',':')).encode())
    except ValueError:
      pass
# malformed duplicate actuation id / malformed actuation interval controls
mal=0
for acts in [[A,A],[Actuation('',1,2,'m','e')],[Actuation('a',3,2,'m','e')]]:
  try: clock_bound(E(actuation_id='a'),acts)
  except ValueError: mal+=1
passed=fp==len(fixed) and pd==pt and mismatch==0 and cross_bound_promoted==0 and cross_numeric_promoted>0 and same_parent_mismatch==0 and mal==3
res={'decision':'PASS_USEFUL_EFFECT_CLOCK_PROVENANCE_GATE_SCOPED' if passed else 'FAIL_USEFUL_EFFECT_CLOCK_PROVENANCE_GATE','fixed_pass':fp,'fixed_total':len(fixed),'parent_degeneration_pass':pd,'parent_degeneration_total':pt,'random_records':N,'candidate_oracle_mismatches':mismatch,'cross_clock_numeric_only_bound_promotions':cross_numeric_promoted,'cross_clock_clock_bound_promotions':cross_bound_promoted,'same_clock_parent_mismatches':same_parent_mismatch,'malformed_controls_pass':mal,'status_counts':status,'digest':h.hexdigest(),'authority_grants':0,'task_input_calls':0,'occupancy_mutations':0}
pathlib.Path('/tmp/ai_exp1004/RESULT.json').write_text(json.dumps(res,indent=2,sort_keys=True)+'\n');print(json.dumps(res,sort_keys=True))
