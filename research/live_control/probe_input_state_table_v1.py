"""Known-trace exact round trips and field-preservation negative controls."""
import copy
import json
from pathlib import Path
from input_state_table_v1 import build,selected,encode,decode,canonical
from report_pages_v2 import digest

HERE=Path(__file__).resolve().parent
out=HERE/'results/input-state-table-01';out.mkdir(exist_ok=False)
paths=['gui-effect-live-01/'+stage+'/report.json' for stage in ('save','recover','resave')]
paths+=['effect-live-03/servo/report.json','effect-live-02/servo/report.json','cause-live-02/interrupt/report.json']
results=[]
for name in paths:
    data=(HERE/'results'/name).read_bytes();source=json.loads(data);rows=selected(source)
    result=build(data)
    assert canonical(decode(result['table']))==canonical(rows)
    results.append(dict(source=name,sha256=digest(data),observations=len(rows),
                        original_selected_bytes=len(canonical(rows).encode()),
                        table_bytes=len(canonical(result['table']).encode()),
                        full_companion_bytes=len(canonical(result).encode())))
    if '/recover/' in name:
        (out/'recovery-table.json').write_text(json.dumps(result,indent=2)+'\n')
baseline=selected(json.loads((HERE/'results/gui-effect-live-01/recover/report.json').read_bytes()))
cases=[]
for name in ('unknown_nested','missing','null','bool_vs_int','int_vs_float','release_failure','owner_change','focus_change','cancelled','empty','duplicate_sequence'):
    rows=copy.deepcopy(baseline)
    first=rows[0]['fields']['input_state_after']
    if name=='unknown_nested':first['unrecognized']={'error':'timeout','verified':False}
    elif name=='missing':del first['owner_id']
    elif name=='null':rows[0]['fields']['input_state_after']=None
    elif name=='bool_vs_int':first['active_lease_time_valid']=1
    elif name=='int_vs_float':first['revision']=float(first['revision'])
    elif name=='release_failure':first['owned_buttons']=[1];first['physical_pointer_mask']=256
    elif name=='owner_change':first['owner_id']='another'
    elif name=='focus_change':first['focus']+=1
    elif name=='cancelled':first['cancel_requested']=True
    elif name=='empty':rows=[]
    elif name=='duplicate_sequence':rows[1]['sequence']=rows[0]['sequence']
    encoded=encode(rows)
    assert canonical(decode(encoded))==canonical(rows),name
    cases.append(name)
output=dict(success=True,sources={n:digest((HERE/n).read_bytes()) for n in ('input_state_table_v1.py','probe_input_state_table_v1.py')},
            traces=results,preservation_controls=cases,
            limits='Same-trace JSON-value round trips of selected fields only. Bytes are not tokens. No new live trial, attention clearance, schema validity, task success or speed comparison.')
(out/'report.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps(output))
