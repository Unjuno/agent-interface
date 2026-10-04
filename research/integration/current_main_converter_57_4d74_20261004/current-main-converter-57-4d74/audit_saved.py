import json,pathlib,hashlib
R=pathlib.Path(__file__).resolve().parent;errors=[]
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def check(ok,label):
    if not ok:errors.append(label)
for entry in json.loads((R/'SOURCE_FREEZE.json').read_text(encoding='utf-8-sig')):
    rel=entry['Path'].split('current-main-converter-57-4d74\\',1)[1]
    check(hashlib.sha256((R/rel).read_bytes()).hexdigest().upper()==entry['Hash'],rel)
source=json.loads((R/'native-first-result.json').read_text(encoding='utf-8-sig'));raw=json.loads((R/'qualification-first.json').read_text(encoding='utf-8-sig'))
check(len(raw['rows'])==4 and raw['native_runs']==raw['model_calls']==0,'scope')
for original,row in zip(source['rows'],raw['rows']):
    check(row['case']==original['case'],'case order')
    check(canonical(row['native_program'])==canonical(original['program']) and canonical(row['native_receipt'])==canonical(original['native_receipt']),'exact original native data')
    check(canonical(row['conversion'])==canonical(original['conversion']),'exact C02/C01 conversion')
    check(row['caller_result']['input_authority']=='consumed_by_recorded_execute_stage','recorded main execute-stage authority')
    check(row['caller_result']['execution_progress'] is None,'main lost/unretained decision progress')
    check(len([e for e in row['events'] if e.get('event')=='adaptive_route_finished'])==1,'one final event')
    if row['case']=='completed':
        check(row['caller_result']['outcome']=='TASK_NOT_VERIFIED' and row['caller_result']['reason']=='unavailable' and row['calls']==['execute','verify'],'completed gate')
    else:
        check(row['caller_result']['outcome']=='CALLER_FAILED' and row['caller_result']['reason']=="ValueError('exact safe_yield execution decision required')" and row['calls']==['execute'],'noncompleted incompatibility')
check(raw['disposition']=='HOLD_CURRENT_MAIN_COMPOSITION' and (R/'EXIT.txt').read_text().strip()=='0','terminal')
print(json.dumps({'errors':errors,'current_main_failures':3,'completed_unverified':1,'scope':'Separate same-author saved byte/type/stage/output check; no converters/caller/native actors imported or replayed. Main composition HOLD, no unsafe-input or task-success claim.'},indent=2));raise SystemExit(bool(errors))
