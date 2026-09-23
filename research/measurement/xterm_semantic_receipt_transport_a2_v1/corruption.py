#!/opt/pyvenv/bin/python3
import copy,json,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).parent)); import audit
obj=json.loads(pathlib.Path(sys.argv[1]).read_text())
controls={}
for name,mut in [
 ('drop_row',lambda x:x['rows'].pop()),
 ('duplicate_id',lambda x:x['rows'].__setitem__(1,{**x['rows'][1],'case_id':x['rows'][0]['case_id']})),
 ('terminal_down',lambda x:x['rows'][0].__setitem__('terminal_key_down',True)),
 ('receipt_invalid',lambda x:x['rows'][0].__setitem__('receipt_valid',False))]:
    y=copy.deepcopy(obj); mut(y); r=audit.audit(y); controls[name]=bool(r['errors'])
print(json.dumps(controls,sort_keys=True))
if not all(controls.values()): raise SystemExit(1)
