import json,sys
rows=[json.loads(x) for x in open(sys.argv[1]) if x.strip()]; errors=[]
for r in rows:
 if r.get('old_receipt_admitted') or r.get('old_receipt_dispatch_count')!=0: errors.append(f"run {r.get('run')}: old receipt accepted/dispatched")
 if r.get('old_receipt_rejection_reason') not in ('generation_mismatch','process_epoch_mismatch'): errors.append(f"run {r.get('run')}: missing reason")
 if not r.get('new_receipt_admitted') or r.get('new_receipt_dispatch_count')!=0: errors.append(f"run {r.get('run')}: new path")
 e=r.get('dom_effect',{})
 if not (e.get('title')=='saved:abc' and e.get('saved')=='true' and e.get('value')=='abc'): errors.append(f"run {r.get('run')}: DOM")
print(f"{'PASS' if not errors else 'HOLD'}_OLD_RECEIPT_ADMISSION rows={len(rows)} errors={len(errors)}")
for e in errors: print('ERROR',e)
raise SystemExit(bool(errors))