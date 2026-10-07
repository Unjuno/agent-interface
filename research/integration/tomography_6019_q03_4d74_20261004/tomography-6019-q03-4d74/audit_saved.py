import pathlib,json,itertools,heapq,hashlib
root=pathlib.Path(__file__).resolve().parent;j=json.loads((root/'first-result.json').read_text(encoding='utf-8-sig'));errors=[]
seen=set();totals={'covariance':[0,0,0,0],'intervention':[0,0,0,0]}
for row in j['rows']:
    routes=row['routes'];caps=row['capacities'];seen.add((tuple(routes),tuple(caps)))
    for label,trace in [('base',row['base'])]+list(row['pulses'].items()):
        slots={s:[0]*caps[i] for i,s in enumerate('PQR')}
        jobs=([(label,'probe',0,8)] if label!='base' else [])+[(s,r,1,2) for r,s in zip('ABC',routes)]
        for e,(s,r,t,duration) in zip(trace,jobs):
            available=heapq.heappop(slots[s]);start=max(available,t);end=start+duration;heapq.heappush(slots[s],end)
            if e!=dict(job=r,offer=t,start=start,end=end,endpoint=end):errors.append('queue')
        if len(trace)!=len(jobs):errors.append('offers')
    for decision in row['decisions']:
        a,b=decision['pair'];control=next(r for r in 'ABC' if r not in (a,b))
        truth=routes['ABC'.index(a)]==routes['ABC'.index(b)]
        base={e['job']:e['endpoint'] for e in row['base']};witness=[]
        for s,trace in row['pulses'].items():
            end={e['job']:e['endpoint'] for e in trace};delta={r:end[r]-base[r] for r in 'ABC'}
            if delta[a]>0 and delta[b]>0 and delta[control]==0:witness.append(s)
        if witness!=decision['witnesses'] or truth!=decision['truth_shared']:errors.append('decision joins')
        for name,claim in [('covariance',True),('intervention',bool(witness))]:
            totals[name][0]+=claim;totals[name][1]+=claim and not truth;totals[name][2]+=claim and truth;totals[name][3]+=not claim
        if decision['covariance']!=20:errors.append('drift covariance')
expected=set(itertools.product(itertools.product('PQR',repeat=3),itertools.product((1,2,3),repeat=3)))
if seen!=expected or len(j['rows'])!=729:errors.append('graph completeness')
metrics={k:dict(zip(['claims','false_edges','true_edges','abstentions'],v)) for k,v in totals.items()}
if metrics!=j['metrics']:errors.append('metrics')
print(json.dumps(dict(errors=errors,graphs=len(seen),metrics=metrics,scope='same-author distinct heap reconstruction; finite authored comparator only'),indent=2));raise SystemExit(bool(errors))
