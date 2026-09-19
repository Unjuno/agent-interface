import json,sys
r=[json.loads(x) for x in open(sys.argv[1]) if x.strip()]; e=[]
for x in r:
 if x.get('old_receipt_admitted') or x['old_effect'] != {'title':'ReceiptFixture','saved':'','value':''}: e.append('old receipt/source mutation')
 if not x.get('new_receipt_admitted') or x['new_effect'] != {'title':'saved:changed','saved':'true','value':'changed'}: e.append('new source effect')
print(f"{'PASS' if not e else 'HOLD'}_SOURCE_INVALIDATION_AUDIT rows={len(r)} errors={len(e)}")
for x in e: print('ERROR',x)
sys.exit(bool(e))
