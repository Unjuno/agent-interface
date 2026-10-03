"""Q02: capacity-aware queue interventions and explicit observational equivalence."""
import heapq,json,pathlib,hashlib
def run(routes,capacity,probe,global_shift=0):
    slots={s:[0]*capacity[s] for s in capacity};trace=[]
    jobs=([('probe','P',0,8)] if probe else [])+[(r,routes[r],1,2) for r in 'ABC']
    for job,service,offer,duration in jobs:
        available=heapq.heappop(slots[service]);start=max(available,offer);end=start+duration
        heapq.heappush(slots[service],end)
        trace.append(dict(job=job,service=service,offer=offer,start=start,end=end,endpoint=end+global_shift))
    return trace
def view(trace):return [{k:v for k,v in event.items() if k!='service'} for event in trace if event['job']!='probe']
def decide(b,p,g,stable):
    if not stable:return 'HOLD_ROUTE_CHANGED'
    deltas={r['job']:s['endpoint']-r['endpoint'] for r,s in zip(b,p)}
    glob={r['job']:s['endpoint']-r['endpoint'] for r,s in zip(b,g)}
    if deltas['C'] or len(set(deltas.values()))==1:return 'UNIDENTIFIED'
    if deltas['A']>0 and deltas['B']>0 and glob['A']==glob['B']==glob['C']:
        return 'COUPLED_AB_UNDER_PROBE'
    return 'UNIDENTIFIED'
definitions=[
 ('serial_shared',dict(A='P',B='P',C='Q'),dict(P=1,Q=1),None),
 ('parallel_shared',dict(A='P',B='P',C='Q'),dict(P=2,Q=1),None),
 ('disjoint',dict(A='P',B='Q',C='R'),dict(P=1,Q=1,R=1),None),
 ('hidden_shared_no_contention',dict(A='P',B='P',C='Q'),dict(P=3,Q=1),None),
 ('hidden_disjoint_equivalent',dict(A='Q',B='R',C='S'),dict(P=1,Q=1,R=1,S=1),None),
 ('switched_route',dict(A='P',B='P',C='Q'),dict(P=1,Q=1),dict(A='P',B='Q',C='Q'))]
rows=[]
for name,routes,cap,changed in definitions:
    base=run(routes,cap,False);probe=run(changed or routes,cap,True);global_control=run(routes,cap,False,8)
    stable=all(routes[r]==(changed or routes)[r] for r in routes)
    result=decide(view(base),view(probe),view(global_control),stable)
    rows.append(dict(case=name,routes=routes,probe_routes=changed or routes,capacity=cap,base=base,probe=probe,global_control=global_control,route_stable=stable,result=result,observable={k:view(v) for k,v in [('base',base),('probe',probe),('global_control',global_control)]}))
by={r['case']:r for r in rows}
equivalent=by['hidden_shared_no_contention']['observable']==by['hidden_disjoint_equivalent']['observable']
print(json.dumps(dict(rows=rows,equivalent_pair=equivalent,source_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),scope='deterministic finite queue interference, not topology certification'),indent=2))
