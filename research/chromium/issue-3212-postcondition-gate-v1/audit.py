import json,sys
r=[json.loads(x) for x in open(sys.argv[1]) if x.strip()]; e=[]
for x in r:
 if not x.get('transport_success') or x.get('postcondition') or x.get('admitted') or x.get('reason')!='contradictory_or_absent_dom': e.append('transport/postcondition gate')
print(f"{'PASS' if not e else 'HOLD'}_POSTCONDITION_GATE_AUDIT rows={len(r)} errors={len(e)}")
for x in e: print('ERROR',x)
sys.exit(bool(e))
