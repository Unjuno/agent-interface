import itertools,json,pathlib,hashlib
def ledger(routes,caps,probe=None,global_shift=0):
    calendars={s:[] for s in 'PQR'};events=[]
    offers=([(str(probe),'probe',0,8)] if probe else [])+[(s,r,1,2) for r,s in zip('ABC',routes)]
    for service,job,offer,duration in offers:
        tick=offer
        while any(sum(a<=t<b for a,b in calendars[service])>=caps['PQR'.index(service)] for t in range(tick,tick+duration)):tick+=1
        calendars[service].append((tick,tick+duration))
        events.append(dict(job=job,offer=offer,start=tick,end=tick+duration,endpoint=tick+duration+global_shift))
    return events
def endpoint(trace):return {e['job']:e['endpoint'] for e in trace if e['job']!='probe'}
rows=[]
for routes in itertools.product('PQR',repeat=3):
    for caps in itertools.product((1,2,3),repeat=3):
        base=ledger(routes,caps);pulses={s:ledger(routes,caps,s) for s in 'PQR'}
        # Frozen common drift panel: same task schedule, all endpoints shifted equally.
        global_panel=[endpoint(ledger(routes,caps,global_shift=k)) for k in (0,4,8,12)]
        b=endpoint(base);decisions=[]
        for a,c in itertools.combinations('ABC',2):
            control=next(r for r in 'ABC' if r not in (a,c))
            witnesses=[]
            for s,p in pulses.items():
                d={r:endpoint(p)[r]-b[r] for r in 'ABC'}
                if d[a]>0 and d[c]>0 and d[control]==0:witnesses.append(s)
            truth=routes['ABC'.index(a)]==routes['ABC'.index(c)]
            # Covariance is calculated explicitly; common drift alone gives positive covariance.
            x=[g[a] for g in global_panel];y=[g[c] for g in global_panel]
            covariance=sum((u-sum(x)/4)*(v-sum(y)/4) for u,v in zip(x,y))/4
            decisions.append(dict(pair=a+c,truth_shared=truth,covariance=covariance,covariance_claim=covariance>0,intervention_claim=bool(witnesses),witnesses=witnesses,disposition='COUPLED_UNDER_PROBE' if witnesses else 'UNIDENTIFIED'))
        rows.append(dict(routes=routes,capacities=caps,base=base,pulses=pulses,global_panel=global_panel,decisions=decisions))
dec=[d for r in rows for d in r['decisions']]
metrics={name:dict(claims=sum(d[field] for d in dec),false_edges=sum(d[field] and not d['truth_shared'] for d in dec),true_edges=sum(d[field] and d['truth_shared'] for d in dec),abstentions=sum(not d[field] for d in dec)) for name,field in [('covariance','covariance_claim'),('intervention','intervention_claim')]}
print(json.dumps(dict(rows=rows,metrics=metrics,graphs=len(rows),pair_decisions=len(dec),source_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()),separators=(',',':')))
