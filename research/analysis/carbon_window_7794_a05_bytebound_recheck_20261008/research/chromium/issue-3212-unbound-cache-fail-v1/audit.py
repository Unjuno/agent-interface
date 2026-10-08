import json,sys
r=[json.loads(x) for x in open(sys.argv[1]) if x.strip()]; unsafe=[]
for x in r:
 if x.get('receipt_source')!=x.get('live_source') and x.get('unbound_admitted') and x.get('effect')=={'title':'saved:unsafe','saved':'true','value':'unsafe'}: unsafe.append(x)
print(f"{'FAIL' if len(unsafe)==len(r) else 'HOLD'}_REUSABLE_RECEIPT_WEAKENS_GATE rows={len(r)} unsafe_witnesses={len(unsafe)}")
sys.exit(0 if len(unsafe)==len(r) else 1)
