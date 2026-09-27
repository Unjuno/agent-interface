import json,sys
r=[json.loads(x) for x in open(sys.argv[1]) if x.strip()];e=[]
for x in r:
 if x.get('old_receipt_admitted') or x.get('old_effect') != {'title':'ReceiptFixture','saved':'','value':''}: e.append('old resource admission/effect')
 if not x.get('new_receipt_admitted') or x.get('new_effect') != {'title':'saved:replacement','saved':'true','value':'replacement'}: e.append('new resource effect')
print(f"{'PASS' if not e else 'HOLD'}_RESOURCE_REPLACEMENT_AUDIT rows={len(r)} errors={len(e)}")
for x in e: print('ERROR',x)
sys.exit(bool(e))
