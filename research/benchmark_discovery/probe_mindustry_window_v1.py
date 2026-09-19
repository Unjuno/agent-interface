"""Archived positive and negative scoring controls; no new gameplay."""
import copy
import hashlib
import json
from pathlib import Path
from mindustry_build_score_v1 import score as old
from mindustry_build_score_v2 import score

HERE=Path(__file__).resolve().parent;source=HERE/'results/mindustry-build-self-use-01'
root=HERE/'results/mindustry-window-01';root.mkdir(exist_ok=False)
read=lambda p:json.loads(p.read_text())
i,d,a=[read(source/n) for n in ('before.json','delivery-before.json','after.json')]
p=read(HERE/'mindustry_flow_plan_v1.json')
assert score(i,d,a,p)==old(i,d,a,p)==read(source/'evaluation.json')
rows=[]
for name in ('nan_tick','positive_infinity','negative_infinity','boolean_tick','reversed_phase','boolean_plans','nan_duration','zero_duration','boolean_copper_goal'):
    initial,delivery,after,plan=copy.deepcopy((i,d,a,p))
    if name=='nan_tick':delivery['tick']=float('nan')
    if name=='positive_infinity':delivery['tick']=float('inf')
    if name=='negative_infinity':delivery['tick']=-float('inf')
    if name=='boolean_tick':delivery['tick']=False
    if name=='reversed_phase':delivery['tick']=initial['tick']-1
    if name=='boolean_plans':delivery['unit']['plans']=False
    if name=='nan_duration':plan['simulation_ticks_min']=float('nan')
    if name=='zero_duration':plan['simulation_ticks_min']=0
    if name=='boolean_copper_goal':plan['minimum_copper_delta']=True
    prior=old(initial,delivery,after,plan);fixed=score(initial,delivery,after,plan)
    assert fixed['status']=='UNKNOWN' and fixed['contract_satisfied'] is None
    # Do not serialize nonfinite numbers as nonstandard JSON.
    rows.append(dict(case=name,old_status=prior['status'],old_satisfied=prior['contract_satisfied'],new=fixed))
negatives=[]
for name in ('zero_delivery','pending_build','short_window','changed_layout'):
    initial,delivery,after=copy.deepcopy((i,d,a))
    if name=='zero_delivery':after['copper']=delivery['copper']
    if name=='pending_build':delivery['unit']['plans']=1
    if name=='short_window':delivery['tick']=after['tick']-1
    if name=='changed_layout':delivery['tiles'][0]['block']='conveyor'
    x=score(initial,delivery,after,p);y=old(initial,delivery,after,p)
    assert x['contract_satisfied'] is y['contract_satisfied']
    negatives.append(dict(case=name,result=x))
report=dict(passed=True,archived_score_unchanged=True,invalid_controls=rows,existing_negatives=negatives,
    sources={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['mindustry_build_score_v1.py','mindustry_build_score_v2.py','probe_mindustry_window_v1.py']},
    inputs={n:hashlib.sha256((source/n).read_bytes()).hexdigest() for n in ['before.json','delivery-before.json','after.json','evaluation.json']},
    scope='Offline measurement validation; actual archived positive unchanged, no new GUI or domain-performance claim.')
(root/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
print(json.dumps(dict(passed=True,invalid_controls=len(rows),old_verified_invalid=[r['case'] for r in rows if r['old_satisfied'] is True])))
