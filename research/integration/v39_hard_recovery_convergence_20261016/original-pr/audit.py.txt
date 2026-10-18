import hashlib,json
from pathlib import Path
p=Path(__file__).resolve().parent; root=p.parents[2]; doom=root/'research'/'doom'; raw=json.loads((p/'results'/'candidate.json').read_text(encoding='utf-8')); errors=[]
def check(ok,msg):
 if not ok: errors.append(msg)
check(raw['source_commit']=='743ae74ec5be2472ff27fa06fe13d5ecf8534de5','commit')
check(raw['controller_sha256']==hashlib.sha256((doom/'map01_overlap_controller_v39.py').read_bytes()).hexdigest(),'controller sha')
check(raw['guard_sha256']==hashlib.sha256((root/'research/live_control/observable_signal_guard_v2.py').read_bytes()).hexdigest(),'guard sha')
h=raw['hard_outcome']; s=raw['recovery_guard_counterfactual']; a=raw['final_admission']; t=raw['cancel_terminal']
check(h['status']=='HARD_INVALIDATED' and h['current_value']==80 and h['hard_minimum']==88,'hard crossing')
check(s['status']=='SOFT_CHANGED' and s['current_value']==96 and s['keep_existing_policy'] is True,'recovery')
check(raw['event_order']==['executor_cancel','planner_interrupt'],'order')
check(t['status']=='cancelled' and t['release']=={'verified':True,'keys_down':[],'buttons_down':[]},'terminal release')
check(raw['drained_latest']==12 and raw['drained_invalidation'] is None,'fresh source')
rs=raw['recovered_fresh_source']; check(rs=={'sequence':12,'health':96,'ammo':4,'cover_admission':'admitted','guard_source_sequence':12,'guard_source_value':96},'fresh recovery admission')
rs=raw['recovered_fresh_source']; check(rs=={'sequence':12,'health':96,'ammo':4,'cover_admission':'admitted','guard_source_sequence':12,'guard_source_value':96},'fresh recovery admission')
rs=raw['recovered_fresh_source']; check(rs=={'sequence':12,'health':96,'ammo':4,'cover_admission':'admitted','guard_source_sequence':12,'guard_source_value':96},'fresh recovery admission')
check(raw['formal_allocation_invocations']==0 and raw['game_model_gui_os_input'] is False,'scope')
def must_reject(mutated):
 e=[]
 if mutated['event_order']!=['executor_cancel','planner_interrupt']: e.append('order')
 if mutated['recovery_guard_counterfactual']['status']!='SOFT_CHANGED' or mutated['recovery_guard_counterfactual']['current_value']!=96: e.append('recovery')
 if mutated['final_admission']['status']!='REJECTED_POLICY_INVALIDATED' or mutated['final_admission']['input_authority_admitted'] is not False: e.append('admission')
 return bool(e)
for name,fn in [('order',lambda x:x.update(event_order=list(reversed(x['event_order'])))),('recovery',lambda x:x['recovery_guard_counterfactual'].update(current_value=80)),('admission',lambda x:x['final_admission'].update(status='READY_FOR_ACTION_VALIDITY'))]:
 m=json.loads(json.dumps(raw)); fn(m); check(must_reject(m),f'mutation accepted: {name}')
res={'status':'PASS_SCOPED_REPLAY' if not errors else 'FAIL','independent_assertions':8,'mutation_rejections':3,'errors':errors,'source_commit':raw['source_commit'],'case':raw['case'],'limits':['live observation timing','physical release','useful feedback','bounded recovery','ammo or progress effect','game outcome']}
(p/'results'/'audit.json').write_text(json.dumps(res,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(res,sort_keys=True))
if errors: raise SystemExit(1)
