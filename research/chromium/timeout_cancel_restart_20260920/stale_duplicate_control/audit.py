import json,sys
r=[json.loads(x) for x in open(sys.argv[1]) if x.strip()];e=[]
for x in r:
 if x.get('journal_loaded')!=3: e.append('journal')
 for k in ('duplicate_replay','stale_replay'):
  q=x.get(k,{})
  if q.get('admitted') or q.get('dispatch_count')!=0 or q.get('effect'): e.append(k)
 if not x.get('fresh_admitted') or x.get('fresh_effect') != {'title':'saved:fresh-after-restart','saved':'true','value':'fresh-after-restart'}: e.append('fresh')
print(f"{'PASS' if not e else 'HOLD'}_STALE_DUPLICATE_RESTART_AUDIT allocations={len(r)} errors={len(e)}")
for x in e: print('ERROR',x)
sys.exit(bool(e))
