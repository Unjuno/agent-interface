import copy,json,pathlib
from converter import convert
R=pathlib.Path(__file__).resolve().parent
saved=json.loads((R/'first-result.json').read_text(encoding='utf-8-sig'));rows=[]
for row in saved['rows']:
    rows.append({'case':'original_'+row['case'],'kind':'exact original data','matches':convert(row['program'],row['native_receipt'])==row['conversion']})
controls=[]
refused=copy.deepcopy(saved['rows'][1]);refused['native_receipt']['program_execution_started']=True;controls.append(('refused_but_started',refused))
completed=copy.deepcopy(saved['rows'][0]);completed['native_receipt']['admission']='refused';controls.append(('completed_but_not_admitted',completed))
failed=copy.deepcopy(saved['rows'][2]);failed['native_receipt']['execution']['completed_ops']=[];failed['native_receipt']['execution'].pop('failed_op');controls.append(('failed_without_failed_operation',failed))
for name,row in controls:
    result={'case':name,'kind':'copied contradiction','program':row['program'],'receipt':row['native_receipt']}
    try:result['accepted']=True;result['conversion']=convert(row['program'],row['native_receipt'])
    except Exception as error:result['accepted']=False;result['error']=repr(error)
    rows.append(result)
false_accepts=sum(row.get('accepted') is True for row in rows if row['kind']=='copied contradiction')
print(json.dumps({'rows':rows,'false_accepts':false_accepts,'disposition':'FAIL_UNTRUSTED_RECEIPT_GATE' if false_accepts else 'PASS_COPIED_CONTRADICTION_GATE','native_runs':0,'model_calls':0},indent=2))
# Execution success does not mean the tested safety property passed.
raise SystemExit(0 if all(row['matches'] for row in rows if row['kind']=='exact original data') else 1)
