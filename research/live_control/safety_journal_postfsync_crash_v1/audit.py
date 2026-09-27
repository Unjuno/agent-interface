import argparse, json, pathlib, sys
from model import canonical,digest,make_receipt
ap=argparse.ArgumentParser(); ap.add_argument('aggregate'); a=ap.parse_args(); agg=json.loads(pathlib.Path(a.aggregate).read_text()); errors=[]
counts={'no_crash':0,'post_fsync_sigkill':0}
for r in agg['rows']:
    cid=r['case_id']; pol=r['policy']; counts[pol]+=1; expected=make_receipt(cid)
    if r['marker']!={'event':'FSYNC_DONE','receipt_id':expected['receipt_id']}: errors.append([cid,'marker'])
    if r['journal']!=[expected]: errors.append([cid,'journal'])
    if r['release_retry_count']!=0 or r['task_action_count']!=0: errors.append([cid,'forbidden_action'])
    if expected['authority']!='none' or expected['task_input_granted'] or expected['action_admission_eligible']: errors.append([cid,'authority'])
    if len(r['final_ledger'])!=1: errors.append([cid,'final_count',len(r['final_ledger'])])
    else:
        lid,ldig,payload=r['final_ledger'][0]
        if lid!=expected['receipt_id'] or ldig!=digest(expected) or json.loads(payload)!=expected: errors.append([cid,'ledger_identity'])
    if r['recovery2']!=[{'receipt_id':expected['receipt_id'],'disposition':'ALREADY_PUBLISHED'}]: errors.append([cid,'recovery2'])
    if r['mutated_recovery']!=[{'receipt_id':expected['receipt_id'],'disposition':'RECEIPT_IDENTITY_CONFLICT'}]: errors.append([cid,'mutated'])
    if pol=='post_fsync_sigkill':
        if r['writer_returncode']!=-9: errors.append([cid,'kill_rc',r['writer_returncode']])
        if r['ledger_before_kill'] or r['ledger_after_writer']: errors.append([cid,'published_before_recovery'])
        if r['recovery1']!=[{'receipt_id':expected['receipt_id'],'disposition':'PUBLISHED'}]: errors.append([cid,'recovery1'])
    else:
        if r['writer_returncode']!=0: errors.append([cid,'writer_rc'])
        if len(r['ledger_before_kill'])!=1 or len(r['ledger_after_writer'])!=1: errors.append([cid,'stable_publish'])
        if r['recovery1']!=[{'receipt_id':expected['receipt_id'],'disposition':'ALREADY_PUBLISHED'}]: errors.append([cid,'recovery1'])
if counts!={'no_crash':5,'post_fsync_sigkill':5}: errors.append(['counts',counts])
if agg.get('formal_invocations')!=1 or agg.get('formal_reruns')!=0: errors.append(['formal_discipline'])
decision='PASS_POSTFSYNC_SAFETY_RECEIPT_CRASH_RECOVERY_SCOPED' if not errors else 'FAIL_INTEGRITY'
out={'decision':decision,'errors':errors,'counts':counts}
print(json.dumps(out,sort_keys=True)); sys.exit(0 if not errors else 1)
