"""Q01 finite queue intervention boundary; hidden graph never passed to inference."""
import json,pathlib,hashlib
R=pathlib.Path(__file__).resolve().parent
def simulate(graph,probe=False,global_delay=False):
    queues={};events=[]
    jobs=([('probe','P',0,8)] if probe else [])+[(r,graph[r],0,2) for r in ('A','B','C')]
    for name,service,offer,duration in jobs:
        start=max(offer,queues.get(service,0));end=start+duration
        queues[service]=end
        events.append(dict(job=name,service=service,offer=offer,start=start,end=end,endpoint=end+(8 if global_delay else 0)))
    return events
def infer(base,intervention,global_control,route_stable=True,probe_authenticated=True):
    # Only public endpoint ledger and eligibility receipts enter the rule.
    if not route_stable or not probe_authenticated:return 'UNIDENTIFIED'
    b={x['job']:x['endpoint'] for x in base if x['job']!='probe'}
    p={x['job']:x['endpoint'] for x in intervention if x['job']!='probe'}
    g={x['job']:x['endpoint'] for x in global_control if x['job']!='probe'}
    delta={k:p[k]-b[k] for k in b};global_delta={k:g[k]-b[k] for k in b}
    if set(delta.values())==set(global_delta.values()):return 'UNIDENTIFIED'
    if delta['C']!=0:return 'UNIDENTIFIED'
    return 'SHARED_AB' if delta['A']>0 and delta['B']>0 else 'NO_SHARED_AB'
def public(events):return [{k:v for k,v in x.items() if k!='service'} for x in events]
cases=[('shared',{'A':'P','B':'P','C':'Q'},True,True),
       ('disjoint',{'A':'P','B':'Q','C':'R'},True,True),
       ('parallel_shared',{'A':'P','B':'P','C':'Q'},True,True),
       ('switched_route',{'A':'P','B':'Q','C':'R'},False,True),
       ('nonidentifiable',{'A':'P','B':'P','C':'P'},True,False)]
rows=[]
for name,graph,stable,authenticated in cases:
    base=simulate(graph);pulse=simulate(graph,True);glob=simulate(graph,False,True)
    observed=infer(public(base),public(pulse),public(glob),stable,authenticated)
    rows.append(dict(case=name,hidden_graph=graph,base=base,pulse=pulse,global_control=glob,route_stable=stable,probe_authenticated=authenticated,result=observed))
    # Same endpoints as the real pulse, but no authenticated localized probe:
    # inference must not manufacture a shared-edge claim.
    rows[-1]['unlabelled_probe_result']=infer(public(base),public(pulse),public(glob),stable,False)
output=dict(rows=rows,source_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),scope='finite authored single-server queue arithmetic; no real service or statistical power claim')
print(json.dumps(output,indent=2))
