"""Fresh saved-data custody checker; does not execute predecessor actors."""
import copy,json,pathlib,itertools
root=pathlib.Path(__file__).resolve().parent
original=json.loads((root/'first-result.json').read_text(encoding='utf-8-sig'))
def validate(j):
    errors=[];seen=set();metrics={k:dict(claims=0,false_edges=0,true_edges=0,abstentions=0) for k in ('covariance','intervention')}
    for row in j['rows']:
        routes=row['routes'];caps=row['capacities'];seen.add((tuple(routes),tuple(caps)))
        base={e['job']:e['endpoint'] for e in row['base']}
        if set(base)!=set('ABC'):errors.append('base jobs');continue
        if len(row['global_panel'])!=4 or any(panel!={r:t+k for r,t in base.items()} for panel,k in zip(row['global_panel'],(0,4,8,12))):errors.append('global panel')
        if set(row['pulses'])!=set('PQR'):errors.append('probe service coverage')
        for trace in row['pulses'].values():
            if sum(e['job']=='probe' for e in trace)!=1 or {e['job'] for e in trace}!=set(['probe','A','B','C']):errors.append('offered probe/task coverage')
            if any(e['endpoint']!=e['end'] or e['end']<=e['start'] or e['start']<e['offer'] for e in trace):errors.append('clock')
        if len(row['decisions'])!=3 or {d['pair'] for d in row['decisions']}!=set(['AB','AC','BC']):errors.append('pair coverage')
        for d in row['decisions']:
            a,b=d['pair'];c=next(r for r in 'ABC' if r not in (a,b));w=[]
            for s,trace in row['pulses'].items():
                end={e['job']:e['endpoint'] for e in trace}
                if not set('ABC').issubset(end):errors.append('task omission');continue
                if end[a]>base[a] and end[b]>base[b] and end[c]==base[c]:w.append(s)
            truth=routes['ABC'.index(a)]==routes['ABC'.index(b)]
            if d['truth_shared']!=truth or d['witnesses']!=w or d['intervention_claim']!=bool(w) or d['disposition']!=('COUPLED_UNDER_PROBE' if w else 'UNIDENTIFIED'):errors.append('claim semantics')
            if d['covariance']!=20 or d['covariance_claim'] is not True:errors.append('covariance')
            for name,claim in [('covariance',True),('intervention',bool(w))]:
                m=metrics[name];m['claims']+=claim;m['false_edges']+=claim and not truth;m['true_edges']+=claim and truth;m['abstentions']+=not claim
    full=set(itertools.product(itertools.product('PQR',repeat=3),itertools.product((1,2,3),repeat=3)))
    if seen!=full or len(j['rows'])!=729 or j['graphs']!=729 or j['pair_decisions']!=2187:errors.append('graph coverage')
    if j['metrics']!=metrics:errors.append('metrics')
    return sorted(set(errors))
results=[dict(case='original',errors=validate(original))]
for case in ['false_claim','false_disposition','clock_offset','missing_probe','wrong_global','missing_graph','wrong_truth','false_metrics']:
    j=copy.deepcopy(original);r=j['rows'][0]
    if case=='false_claim':r['decisions'][0]['intervention_claim']=not r['decisions'][0]['intervention_claim']
    elif case=='false_disposition':r['decisions'][0]['disposition']='COUPLED_UNDER_PROBE'
    elif case=='clock_offset':r['pulses']['P'][1]['endpoint']+=1
    elif case=='missing_probe':r['pulses']['P'].pop(0)
    elif case=='wrong_global':r['global_panel'][0]['A']+=1
    elif case=='missing_graph':j['rows'].pop()
    elif case=='wrong_truth':r['decisions'][0]['truth_shared']=False
    elif case=='false_metrics':j['metrics']['intervention']['false_edges']=1
    results.append(dict(case=case,errors=validate(j)))
print(json.dumps(dict(results=results,scope='new same-author checker qualification, not predecessor actor replay or original historical audit regrading'),indent=2))
raise SystemExit(bool(results[0]['errors']) or any(not r['errors'] for r in results[1:]))
