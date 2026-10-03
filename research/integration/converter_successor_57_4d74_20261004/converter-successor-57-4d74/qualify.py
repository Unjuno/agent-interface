import copy,json,pathlib
from legacy_converter import convert as old
from strict_converter import convert as new
R=pathlib.Path(__file__).resolve().parent;saved=json.loads((R/'native-first-result.json').read_text(encoding='utf-8-sig'));rows=[]
for row in saved['rows']:
    converted=new(row['program'],row['native_receipt']);rows.append({'case':'original_'+row['case'],'kind':'original','program':row['program'],'receipt':row['native_receipt'],'conversion':converted,'unchanged':converted==row['conversion']})
controls=[]
def add(name,index,edit):
    row=copy.deepcopy(saved['rows'][index]);edit(row['native_receipt']);controls.append((name,row))
add('refused_but_started',1,lambda r:r.update(program_execution_started=True))
add('completed_but_not_admitted',0,lambda r:r.update(admission='refused'))
def missing_failed(r):r['execution']['completed_ops']=[];r['execution'].pop('failed_op')
add('failed_without_failed_operation',2,missing_failed)
add('bool_prefix',0,lambda r:r['execution'].update(completed_ops=[False,1,2]))
add('missing_recovery_flag',0,lambda r:r.pop('recovery_required'))
add('bool_failed_operation',2,lambda r:r['execution'].update(failed_op=True))
add('reversed_clock',0,lambda r:r['execution'].update(ended_ns=r['execution']['started_ns']-1))
for name,row in controls:
    result={'case':name,'kind':'copy','program':row['program'],'receipt':row['native_receipt']}
    for label,fn in [('old',old),('new',new)]:
        try:result[label]={'accepted':True,'conversion':fn(row['program'],row['native_receipt'])}
        except Exception as error:result[label]={'accepted':False,'error':repr(error)}
    rows.append(result)
ok=all(row['unchanged'] for row in rows if row['kind']=='original') and all(row['new']['accepted'] is False for row in rows if row['kind']=='copy')
print(json.dumps({'rows':rows,'disposition':'PASS_SEVEN_CONSISTENCY_CONTROLS_SCOPED' if ok else 'FAIL_CONSISTENCY_WRAPPER','native_runs':0,'model_calls':0},indent=2));raise SystemExit(not ok)
