import json,sys
rows=[json.loads(x) for x in open(sys.argv[1]) if x.strip()]
b=[r for r in rows if r.get('role')=='B']; errors=[]
if len(b)!=3: errors.append('expected 3 B rows')
for r in b:
 if r.get('old_receipt_admitted') or r.get('old_receipt_effect')!='ReceiptFixture': errors.append(f"run {r.get('run')}: old receipt admission/effect")
 if not r.get('new_receipt_admitted'): errors.append(f"run {r.get('run')}: new receipt not admitted")
 if not (r.get('new_generation')==2 and r.get('process_start',0)>0): errors.append(f"run {r.get('run')}: generation/epoch")
 e=r.get('dom_effect',{})
 if not (e.get('title')=='saved:abc' and e.get('saved')=='true' and e.get('value')=='abc'): errors.append(f"run {r.get('run')}: DOM effect")
print(f"{'PASS' if not errors else 'HOLD'}_ORCHESTRATOR_RESTORE_AUDIT rows={len(rows)} allocations={len(b)} errors={len(errors)}")
for e in errors: print('ERROR',e)
sys.exit(bool(errors))
