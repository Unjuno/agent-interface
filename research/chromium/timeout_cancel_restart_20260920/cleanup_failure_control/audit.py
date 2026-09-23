import json,sys
r=[json.loads(x) for x in open(sys.argv[1]) if x.strip()];e=[]
for x in r:
 if x.get('journal_loaded')!=2 or not x.get('cleanup_release_verified'): e.append('journal/cleanup')
 t=x.get('terminal_replay',{})
 if t.get('admitted') or t.get('dispatch_count')!=0 or t.get('effect') or t.get('reason')!='cleanup_release_failed': e.append('terminal replay')
 if not x.get('fresh_admitted') or x.get('fresh_effect') != {'title':'saved:fresh-cleanup','saved':'true','value':'fresh-cleanup'}: e.append('fresh effect')
print(f"{'PASS' if not e else 'HOLD'}_CLEANUP_FAILURE_RESTART_AUDIT allocations={len(r)} errors={len(e)}")
for x in e: print('ERROR',x)
sys.exit(bool(e))
