import json,pathlib,hashlib
root=pathlib.Path(__file__).resolve().parent
j=json.loads((root/'first-result.json').read_text(encoding='utf-8-sig'));errors=[]
if hashlib.sha256((root/'experiment.py').read_bytes()).hexdigest()!=j['source_sha256']:errors.append('source identity')
for row in j['rows']:
    for label in ['base','probe','global_control']:
        reservations={s:[] for s in row['capacity']}
        for e in row[label]:
            # Tick enumeration independent of producer's heap slots.
            duration=8 if e['job']=='probe' else 2
            tick=e['offer']
            while any(sum(a<=t<b for a,b in reservations[e['service']])>=row['capacity'][e['service']] for t in range(tick,tick+duration)):
                tick+=1
            end=tick+duration
            if (tick,end,end+(8 if label=='global_control' else 0))!=(e['start'],e['end'],e['endpoint']):errors.append(row['case']+':'+label+':'+e['job'])
            reservations[e['service']].append((tick,end))
    continuity=row['routes']==row['probe_routes']
    if continuity!=row['route_stable']:errors.append('route continuity')
    expected='COUPLED_AB_UNDER_PROBE' if row['case']=='serial_shared' else 'HOLD_ROUTE_CHANGED' if row['case']=='switched_route' else 'UNIDENTIFIED'
    if row['result']!=expected:errors.append('decision:'+row['case'])
by={r['case']:r for r in j['rows']}
if by['hidden_shared_no_contention']['observable']!=by['hidden_disjoint_equivalent']['observable']:errors.append('equal observation pair')
p={e['job']:e for e in by['parallel_shared']['base']}
if max(p['A']['start'],p['B']['start'])>=min(p['A']['end'],p['B']['end']):errors.append('parallel overlap absent')
if by['serial_shared']['base']==by['parallel_shared']['base']:errors.append('parallel contrast duplicate')
print(json.dumps(dict(errors=errors,cases=6,equivalent_pair=True,disposition='SUPPORT_FINITE_NONIDENTIFIABILITY; HOLD_FULL_T0',scope='same author distinct tick enumerator, not nonauthor review; supplied route metadata'),indent=2))
raise SystemExit(bool(errors))
