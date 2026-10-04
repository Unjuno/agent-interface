import json,pathlib,hashlib
root=pathlib.Path(__file__).resolve().parent
j=json.loads((root/'first-result.json').read_text(encoding='utf-8-sig'))
freeze=json.loads((root/'SOURCE_FREEZE.json').read_text(encoding='utf-8-sig'))
sha=hashlib.sha256((root/'experiment.py').read_bytes()).hexdigest();errors=[]
if sha!=j['source_sha256'] or sha.upper()!=freeze['Hash']:errors.append('source freeze mismatch')
if (root/'EXIT.txt').read_text(encoding='utf-8-sig').strip()!='0':errors.append('producer exit')
if (root/'AUDIT_EXIT.txt').read_text(encoding='utf-8-sig').strip()!='0':errors.append('first audit exit')
if json.loads((root/'audit-first.json').read_text(encoding='utf-8-sig'))['errors']:errors.append('first audit errors')
total_delay=0;max_delay=0;probes=0;tasks=0;baseline_tasks=0;control_tasks=0;endpoints_preserved=0
for row in j['rows']:
    base={e['job']:e['endpoint'] for e in row['base']};baseline_tasks+=len(base)
    if len(row['global_panel'])!=4:errors.append('global panel count')
    for shift,panel in zip((0,4,8,12),row['global_panel']):
        if panel!={r:t+shift for r,t in base.items()}:errors.append('global control')
        control_tasks+=len(panel)
    for pair in row['decisions']:
        a,b=pair['pair'];x=[p[a] for p in row['global_panel']];y=[p[b] for p in row['global_panel']]
        covariance=sum(xi*yi for xi,yi in zip(x,y))/4-(sum(x)/4)*(sum(y)/4)
        if covariance!=pair['covariance'] or pair['covariance_claim']!=(covariance>0):errors.append('covariance actual panel')
    for service,trace in row['pulses'].items():
        p=[e for e in trace if e['job']=='probe'];task=[e for e in trace if e['job']!='probe']
        if len(p)!=1 or p[0]['end']-p[0]['start']!=8:errors.append('probe offer')
        probes+=len(p);tasks+=len(task)
        if {e['job'] for e in task}!=set('ABC'):errors.append('missing offered task')
        for e in task:
            delay=e['endpoint']-base[e['job']]
            if delay<0:errors.append('unexpected probe speedup')
            total_delay+=delay;max_delay=max(max_delay,delay)
            endpoints_preserved+=e['end']-e['start']==2
print(json.dumps(dict(errors=errors,source_sha256=sha,graphs=len(j['rows']),baseline_tasks=baseline_tasks,global_control_tasks=control_tasks,probe_jobs=probes,probed_tasks=tasks,service_duration_preserved=endpoints_preserved,aggregate_probe_added_endpoint_ticks=total_delay,max_probe_added_endpoint_ticks=max_delay,probe_service_ticks=probes*8,scope='synthetic workload cost only; unchanged duration is not independent task-effect correctness; same-author saved-only supplement'),indent=2))
raise SystemExit(bool(errors))
