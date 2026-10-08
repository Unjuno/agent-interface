import itertools,json
from pathlib import Path
OUT=Path(__file__).resolve().parent
SOURCE={'sequence':10,'capture_ns':1_000_000_000,'binding':(11,22,(0,0,640,480)),'health':73,'ammo':45}
contracts={'retreat':{'max_age':1000,'preds':[('health','minimum',30),('health','max_decrease',6),('ammo','minimum',1)]},'strafe':{'max_age':1000,'preds':[('health','minimum',30),('health','max_decrease',6)]}}
def eval_contract(contract,snapshot):
 if snapshot['binding']!=SOURCE['binding']:return 'REJECTED_STATE_BINDING'
 if snapshot['sequence']<SOURCE['sequence'] or snapshot['capture_ns']<SOURCE['capture_ns']:return 'REJECTED_SEQUENCE'
 if snapshot['decided_ns']<snapshot['capture_ns']:return 'INVALID_CLOCK'
 if (snapshot['decided_ns']-snapshot['capture_ns'])/1e6>contract['max_age']:return 'REJECTED_STALE'
 for sid,op,expected in contract['preds']:
  cur=snapshot['signals'].get(sid)
  if cur is None or cur[0]!='observed':return 'REJECTED_SIGNAL_UNKNOWN'
  obs=cur[1]
  try:
   passed=obs>=expected if op=='minimum' else obs<=expected if op=='maximum' else type(obs) is type(expected) and obs==expected if op=='equals' else obs>=SOURCE[sid]-expected
  except TypeError:passed=False
  if not passed:return 'REJECTED_PREDICATE'
 return 'VALID_CURRENT'
health_vals=[('unknown',None),('observed',20),('observed',30),('observed',66),('observed',67),('observed',68),('observed',73),('observed',80)]
ammo_vals=[('unknown',None),('observed',0),('observed',1),('observed',45)]
binds=[SOURCE['binding'],(11,22,(1,0,640,480))];seqs=[9,10,11];ages=[10,1000,1001]
rows=[];mismatches=[];omission=[]
for name,c in contracts.items():
 req=sorted({p[0] for p in c['preds']});n=0
 for h,a,b,seq,age in itertools.product(health_vals,ammo_vals,binds,seqs,ages):
  signals={'health':h,'ammo':a,'irrelevant':('observed',999)};snap={'sequence':seq,'capture_ns':1_100_000_000,'binding':b,'decided_ns':1_100_000_000+age*1_000_000,'signals':signals}
  full=eval_contract(c,snap);proj=eval_contract(c,{**snap,'signals':{k:signals[k] for k in req}});n+=1
  if full!=proj:mismatches.append([name,h,a,b,seq,age,full,proj])
 good={'sequence':11,'capture_ns':1_100_000_000,'binding':SOURCE['binding'],'decided_ns':1_110_000_000,'signals':{'health':('observed',73),'ammo':('observed',45),'irrelevant':('observed',999)}}
 for omit in req:
  remaining={k:v for k,v in good['signals'].items() if k in req and k!=omit}
  if not remaining:remaining={'irrelevant':('observed',999)}
  omission.append({'contract':name,'omitted':omit,'status':eval_contract(c,{**good,'signals':remaining})})
 rows.append({'contract':name,'required_signals':req,'finite_cases':n})
assert not mismatches
assert all(x['status']=='REJECTED_SIGNAL_UNKNOWN' for x in omission)
result={'pass':True,'contracts':rows,'mismatches':mismatches,'omission_ablation':omission,'total_finite_cases':sum(r['finite_cases'] for r in rows)}
(OUT/'action_validity_projection_results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
