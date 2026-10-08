import json,sys
r=[json.loads(x) for x in open(sys.argv[1]) if x.strip()]; e=[]
for x in r:
 if x.get('first_effect') != {'title':'saved:first','saved':'true','value':'first'}: e.append('first effect')
 if x.get('replay_admitted') or x.get('replay_effect') != {'title':'saved:first','saved':'true','value':'first'}: e.append('replay changed state')
print(f"{'PASS' if not e else 'HOLD'}_DUPLICATE_REPLAY_AUDIT rows={len(r)} errors={len(e)}")
for x in e: print('ERROR',x)
sys.exit(bool(e))
