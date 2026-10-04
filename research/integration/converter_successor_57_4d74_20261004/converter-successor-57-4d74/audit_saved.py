import json,pathlib,hashlib,copy
R=pathlib.Path(__file__).resolve().parent;errors=[]
def text(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def check(ok,label):
    if not ok:errors.append(label)
for entry in json.loads((R/'SOURCE_FREEZE.json').read_text(encoding='utf-8-sig')):
    rel=entry['Path'].split('converter-successor-57-4d74\\',1)[1]
    check(hashlib.sha256((R/rel).read_bytes()).hexdigest().upper()==entry['Hash'],rel)
original=json.loads((R/'native-first-result.json').read_text(encoding='utf-8-sig'));saved=json.loads((R/'qualification-first.json').read_text(encoding='utf-8-sig'))
check(len(saved['rows'])==11 and saved['native_runs']==saved['model_calls']==0,'scope')
for source,row in zip(original['rows'],saved['rows'][:4]):
    check(row['case']=='original_'+source['case'],'original case order')
    check(text(row['program'])==text(source['program']) and text(row['receipt'])==text(source['native_receipt']),'original inputs')
    check(text(row['conversion'])==text(source['conversion']) and row['unchanged'] is True,'full unchanged original conversion')
indices=[1,0,2,0,0,2,0];names=['refused_but_started','completed_but_not_admitted','failed_without_failed_operation','bool_prefix','missing_recovery_flag','bool_failed_operation','reversed_clock']
copies=[copy.deepcopy(original['rows'][i]) for i in indices]
copies[0]['native_receipt']['program_execution_started']=True
copies[1]['native_receipt']['admission']='refused'
copies[2]['native_receipt']['execution']['completed_ops']=[];copies[2]['native_receipt']['execution'].pop('failed_op')
copies[3]['native_receipt']['execution']['completed_ops']=[False,1,2]
copies[4]['native_receipt'].pop('recovery_required')
copies[5]['native_receipt']['execution']['failed_op']=True
copies[6]['native_receipt']['execution']['ended_ns']=copies[6]['native_receipt']['execution']['started_ns']-1
for index,(name,source,row) in enumerate(zip(names,copies,saved['rows'][4:])):
    check(row['case']==name and text(row['program'])==text(source['program']) and text(row['receipt'])==text(source['native_receipt']),'exact copied change '+name)
    check(row['new']['accepted'] is False and row['new']['error'].startswith('ValueError('),'new refusal '+name)
    if index<3:check(row['old']['accepted'] is True,'retained predecessor failure '+name)
check(saved['disposition']=='PASS_SEVEN_CONSISTENCY_CONTROLS_SCOPED' and (R/'EXIT.txt').read_text().strip()=='0','terminal')
print(json.dumps({'errors':errors,'original_conversions_equal':4,'copied_controls_refused':7,'scope':'Complete saved original/copy data comparisons and source hashes; same author, no converters/native/caller imported or replayed, no authority/authenticity/task qualification.'},indent=2))
raise SystemExit(bool(errors))
