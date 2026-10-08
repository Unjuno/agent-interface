import json,sys
r=[json.loads(x) for x in open(sys.argv[1]) if x.strip()];e=[]
for x in r:
 if x.get('journal_loaded')!=3 or not x.get('xlib_loaded'): e.append('journal/xlib')
 if len(x.get('terminal_replay',[]))!=2 or any(y.get('admitted') or y.get('dispatch_count')!=0 or y.get('effect') for y in x['terminal_replay']): e.append('terminal replay')
 if not x.get('fresh_admitted') or x.get('fresh_effect') != {'title':'saved:fresh','saved':'true','value':'fresh'}: e.append('fresh valid')
print(f"{'PASS' if not e else 'HOLD'}_TIMEOUT_CANCEL_RESTART_AUDIT allocations={len(r)} terminal_replays={sum(len(x.get('terminal_replay',[])) for x in r)} errors={len(e)}")
for x in e: print('ERROR',x)
sys.exit(bool(e))
