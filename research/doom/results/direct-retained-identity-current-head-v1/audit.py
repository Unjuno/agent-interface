"""Independent oracle for the direct analyzer's frozen token/key cases."""
import argparse, hashlib, json, sys
from collections import defaultdict, deque
from pathlib import Path
HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(); parser.add_argument('--results',type=Path,default=HERE/'candidate_results.json'); parser.add_argument('--out',type=Path,default=HERE/'audit.json'); args=parser.parse_args()
if args.out.exists(): raise FileExistsError(f'refusing to overwrite {args.out}')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
freeze=json.loads((HERE/'FREEZE.json').read_text(encoding='utf-8')); raw=json.loads((HERE/'raw_cases.json').read_text(encoding='utf-8')); candidate=json.loads(args.results.read_text(encoding='utf-8')); errors=[]
for key,name in [('analyzer_sha256','analyzer.py'),('tests_sha256','tests.py'),('raw_sha256','raw_cases.json'),('candidate_runner_sha256','candidate.py'),('auditor_sha256','audit.py')]:
    if sha(HERE/name)!=freeze[key]: errors.append({'error':'frozen_identity_mismatch','field':key})
if candidate.get('schema')!='direct-retained-token-key-candidate-v1': errors.append({'error':'candidate_schema_mismatch'})
if candidate.get('analyzer_sha256')!=freeze['analyzer_sha256'] or candidate.get('tests_sha256')!=freeze['tests_sha256']: errors.append({'error':'candidate_source_identity_mismatch'})
results=candidate.get('results',[]); cases=raw.get('cases',[])
if candidate.get('case_count')!=len(cases) or len(results)!=len(cases): errors.append({'error':'case_count_mismatch'})
if [x.get('case_id') for x in results] != [x.get('case_id') for x in cases]: errors.append({'error':'case_coverage_mismatch'})
def oracle(events):
    pending=defaultdict(deque); holds=[]; invalid_admissions=0; invalid_releases=0
    for row in events:
        if row.get('event')=='input_admission':
            token,key=row.get('intent_token'),row.get('key')
            if type(token) is not str or not token or type(key) is not str or not key: invalid_admissions+=1; continue
            pending[(token,key)].append(row)
        elif row.get('event')=='input_release_transition' and row.get('operation')=='up':
            token,key=row.get('intent_token'),row.get('key')
            if type(token) is not str or not token or type(key) is not str or not key: invalid_releases+=1; continue
            q=pending[(token,key)]
            if not q or row.get('owner_transition_verified') is not True: invalid_releases+=1; continue
            start=q.popleft(); times=(start.get('admitted_ns'),start.get('input_ack_ns'),row.get('release_call_started_ns'),row.get('release_call_returned_ns'))
            if any(type(t) is not int for t in times): invalid_releases+=1; continue
            admitted,ack,release_start,release_return=times
            if not admitted<=ack<=release_start<=release_return: invalid_releases+=1; continue
            lower=release_start-ack; upper=release_return-admitted
            holds.append({'intent_token':token,'key':key,'retained_lower_ms':lower/1e6,'retained_upper_ms':upper/1e6,'censor_width_ms':(upper-lower)/1e6,'source_events':['input_admission','input_release_transition']})
    unmatched=sum(len(q) for q in pending.values())
    ready=bool(holds) and not unmatched and not invalid_releases and not invalid_admissions
    return {'measurement_ready':ready,'hold_count':len(holds),'unmatched_admission_count':unmatched,'invalid_release_count':invalid_releases,'invalid_admission_count':invalid_admissions,'holds':holds,'decision':'PASS: direct bounded release evidence available' if ready else 'FAIL: retained-input duration is not identifiable from this trace'}
for case,result in zip(cases,results):
    expected=oracle(case['events']); actual=result.get('result',{})
    for field,value in expected.items():
        if actual.get(field)!=value: errors.append({'error':'candidate_result_mismatch','case_id':case['case_id'],'field':field,'expected':value,'got':actual.get(field)}); break
report={'schema':'direct-retained-token-key-audit-v1','analyzer_sha256':sha(HERE/'analyzer.py'),'tests_sha256':sha(HERE/'tests.py'),'raw_sha256':sha(HERE/'raw_cases.json'),'candidate_sha256':sha(args.results),'case_count':len(cases),'ready_cases':sum(bool(x.get('result',{}).get('measurement_ready')) for x in results),'fail_closed_case_count':sum(not bool(x.get('result',{}).get('measurement_ready')) for x in results),'errors':errors,'decision':'PASS_TOKEN_KEY_IDENTITY_FAIL_CLOSED' if not errors else 'FAIL'}
args.out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8'); print(json.dumps(report,indent=2)); sys.exit(1 if errors else 0)
