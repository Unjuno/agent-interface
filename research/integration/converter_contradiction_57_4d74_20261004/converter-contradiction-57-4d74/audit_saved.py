import json,pathlib,hashlib,copy
R=pathlib.Path(__file__).resolve().parent;errors=[]
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def check(ok,label):
    if not ok:errors.append(label)
for entry in json.loads((R/'SOURCE_FREEZE.json').read_text(encoding='utf-8-sig')):
    rel=entry['Path'].split('converter-contradiction-57-4d74\\',1)[1]
    check(hashlib.sha256((R/rel).read_bytes()).hexdigest().upper()==entry['Hash'],rel)
original=json.loads((R/'first-result.json').read_text(encoding='utf-8-sig'));saved=json.loads((R/'qualification-first.json').read_text(encoding='utf-8-sig'))
check(len(original['rows'])==4 and original['errors']==[],'original scope')
check(len(saved['rows'])==7 and saved['native_runs']==saved['model_calls']==0,'offline scope')
expected=[]
a=copy.deepcopy(original['rows'][1]);a['native_receipt']['program_execution_started']=True;expected.append(a)
b=copy.deepcopy(original['rows'][0]);b['native_receipt']['admission']='refused';expected.append(b)
c=copy.deepcopy(original['rows'][2]);c['native_receipt']['execution']['completed_ops']=[];c['native_receipt']['execution'].pop('failed_op');expected.append(c)
for row in saved['rows'][:4]:check(row['matches'] is True,'original mapping equality')
for row,expectedrow in zip(saved['rows'][4:],expected):
    check(row['accepted'] is True,'retained false accept')
    check(canonical(row['program'])==canonical(expectedrow['program']) and canonical(row['receipt'])==canonical(expectedrow['native_receipt']),'exact copied perturbation')
    check(canonical(row['conversion']['native_receipt'])==canonical(row['receipt']),'whole copied receipt custody')
    check(row['conversion']['native_receipt_sha256']==hashlib.sha256(canonical(row['receipt']).encode()).hexdigest(),'copied digest')
check(saved['rows'][4]['conversion']['decision']['input_dispatched'] is False and saved['rows'][4]['receipt']['program_execution_started'] is True,'started/refused contradiction')
check(saved['rows'][5]['conversion']['decision']=={'status':'completed'} and saved['rows'][5]['receipt']['admission']=='refused','completion/admission contradiction')
check(saved['rows'][6]['conversion']['decision']['input_dispatched'] is False and 'failed_op' not in saved['rows'][6]['receipt']['execution'],'unknown failed operation')
check(saved['false_accepts']==3 and saved['disposition']=='FAIL_UNTRUSTED_RECEIPT_GATE','scientific failure retention')
check((R/'EXIT.txt').read_text().strip()=='0','qualification execution exit')
print(json.dumps({'errors':errors,'false_accepts_retained':3,'scope':'Saved complete copied perturbation/type/custody checks; same author, no converter/native actor imports or replay. Original producer scope not regraded.'},indent=2))
raise SystemExit(bool(errors))
