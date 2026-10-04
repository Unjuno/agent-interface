"""Distinct saved-ledger enumerator; never imports or runs producer."""
import pathlib,json,hashlib
root=pathlib.Path(__file__).resolve().parent
data=json.loads((root/'first-result.json').read_text(encoding='utf-8-sig'))
errors=[];findings=[]
if hashlib.sha256((root/'experiment.py').read_bytes()).hexdigest()!=data['source_sha256']:errors.append('producer source identity')
for row in data['rows']:
    for key in ['base','pulse','global_control']:
        events=row[key]
        # Independently sum preceding durations for each service in FIFO offer order.
        for i,event in enumerate(events):
            prior=[e for e in events[:i] if e['service']==event['service']]
            start=sum(e['end']-e['start'] for e in prior)
            duration=8 if event['job']=='probe' else 2
            if (event['start'],event['end'],event['endpoint'])!=(start,start+duration,start+duration+(8 if key=='global_control' else 0)):
                errors.append(row['case']+':'+key+':'+event['job'])
    if row['unlabelled_probe_result']!='UNIDENTIFIED':errors.append('unauthenticated probe promoted')
    expected={'shared':'SHARED_AB','disjoint':'NO_SHARED_AB','parallel_shared':'SHARED_AB','switched_route':'UNIDENTIFIED','nonidentifiable':'UNIDENTIFIED'}[row['case']]
    if row['result']!=expected:errors.append('classification:'+row['case'])
lookup={x['case']:x for x in data['rows']}
if all(lookup['shared'][k]==lookup['parallel_shared'][k] for k in ['hidden_graph','base','pulse','global_control']):
    findings.append('parallel_shared is byte-value-identical to serial shared schedules; no overlap contrast')
findings.extend(['route_stable is supplied eligibility flag, not actual observed route transition','nonidentifiability is supplied authentication refusal, not paired indistinguishable graph enumeration','no covariance-only baseline, statistical power or full Issue T0 mutation set'])
print(json.dumps(dict(errors=errors,arithmetic_rows=5,coverage_findings=findings,disposition='PASS_SAVED_ARITHMETIC; HOLD_ISSUE_T0_COVERAGE',independence='same author distinct algorithm; no nonauthor or blind review'),indent=2))
raise SystemExit(bool(errors))
