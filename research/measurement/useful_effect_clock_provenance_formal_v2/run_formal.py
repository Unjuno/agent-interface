from __future__ import annotations
import hashlib,json
from pathlib import Path
from candidate import Actuation,Effect,clock_bound
from oracle_independent import classify,parent988
from corpus import cases,COUNTS,SEED
HERE=Path(__file__).resolve().parent; OUT=HERE/'FORMAL_RESULT.json'
if OUT.exists(): raise RuntimeError('formal result exists')
N=sum(COUNTS.values()); equal=0; same_mismatch=0; cross_promotions=0; status={}; digest=hashlib.sha256(); strata={k:0 for k in COUNTS}
for stratum,e,acts in cases():
    c=clock_bound(e,acts); o=classify(e,acts); equal += c==o; strata[stratum]+=1; status[c]=status.get(c,0)+1
    if stratum=='same_clock': same_mismatch += c!=parent988(e,acts)
    if stratum in ('cross_domain','cross_epoch','missing_clock') and c in ('useful_bound','nonuseful_bound'): cross_promotions+=1
    digest.update(json.dumps([stratum,e.__dict__,[a.__dict__ for a in acts],c],sort_keys=True,separators=(',',':')).encode())
A=Actuation('a',10,14,'mono','ep1'); E=Effect('e','a',20,True,True,'mono','ep1')
controls=[]
def expect(name, expected, fn):
    try: got=fn(); ok=(got==expected)
    except Exception as ex: got=type(ex).__name__; ok=(expected=='ValueError' and isinstance(ex,ValueError))
    controls.append({'name':name,'expected':expected,'got':got,'pass':ok})
expect('same_before','invalid_temporal',lambda:clock_bound(Effect('e','a',9,True,True,'mono','ep1'),[A]))
expect('same_inside','temporal_ambiguous',lambda:clock_bound(Effect('e','a',12,True,True,'mono','ep1'),[A]))
expect('same_after','useful_bound',lambda:clock_bound(E,[A]))
expect('cross_domain','temporal_clock_mismatch',lambda:clock_bound(Effect('e','a',20,True,True,'other','ep1'),[A]))
expect('cross_epoch','temporal_clock_mismatch',lambda:clock_bound(Effect('e','a',20,True,True,'mono','ep2'),[A]))
expect('missing_effect_clock','temporal_clock_unknown',lambda:clock_bound(Effect('e','a',20,True,True,None,'ep1'),[A]))
expect('negative_precedence','invalid_temporal',lambda:clock_bound(Effect('e','a',-1,True,True,'other','ep2'),[A]))
expect('unscored_precedence','unscored',lambda:clock_bound(Effect('e','a',20,False,True,'other','ep2'),[A]))
expect('unbound_useful','useful_unbound',lambda:clock_bound(Effect('e',None,20,True,True,'other','ep2'),[A]))
expect('unbound_nonuseful','nonuseful_unbound',lambda:clock_bound(Effect('e','unknown',20,True,False,'other','ep2'),[A]))
expect('duplicate_actuation','ValueError',lambda:clock_bound(E,[A,A]))
expect('empty_actuation','ValueError',lambda:clock_bound(E,[Actuation('',1,2,'m','e')]))
expect('reversed_interval','ValueError',lambda:clock_bound(E,[Actuation('a',3,2,'m','e')]))
controls_pass=sum(x['pass'] for x in controls)
passed=(equal==N and same_mismatch==0 and cross_promotions==0 and controls_pass==len(controls))
r={'task':'USEFUL-EFFECT-CLOCK-PROVENANCE-FORMAL-20260917-002','candidate_git_blob':'b8e35581eaf1f99f6ad973f4bde1367e43eb0a1b','seed':SEED,'formal_invocations':1,'reruns':0,'records':N,'strata':strata,'candidate_oracle_equal':equal,'same_clock_parent_mismatches':same_mismatch,'cross_clock_bound_promotions':cross_promotions,'controls_passed':controls_pass,'controls_total':len(controls),'controls':controls,'status_counts':status,'digest_sha256':digest.hexdigest(),'model_calls':0,'network_actions':0,'task_input_actions':0,'authority_actions':0,'occupancy_mutations':0,'decision':'PASS_USEFUL_EFFECT_CLOCK_PROVENANCE_FORMAL_SCOPED' if passed else 'FAIL_CLOCK_PROVENANCE_FORMAL'}
OUT.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,sort_keys=True))
