"""Versioned post-run saved-only audit qualification, original STOP immutable."""
import copy,hashlib,json
from pathlib import Path
from auditor import analyze
def materially_changed(original,changed):
    return json.dumps(original,sort_keys=True,separators=(',',':'),allow_nan=False)!=json.dumps(changed,sort_keys=True,separators=(',',':'),allow_nan=False)
def main():
    root=Path(__file__).parent
    freeze=json.loads((root/'FREEZE.json').read_text())
    for name,digest in freeze['sha256'].items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
    raw=(root/'runs/candidate/raw.jsonl').read_bytes();digest=hashlib.sha256(raw).hexdigest()
    first=json.loads((root/'runs/auditor/AUDIT.json').read_text())
    assert first['status']=='STOP_INVALID_NATIVE_EVIDENCE'and first['error']=="ValueError('effective control')"and first['raw_sha256']==digest
    rows=[json.loads(x)for x in raw.splitlines()];result=analyze(rows)
    mutations={
      'swallowed_ABA':lambda x:x[1].__setitem__('events_through_F',[]),
      'forged_subscription':lambda x:x[3]['subscription'].__setitem__('covered',True),
      'quiet_to_authority':lambda x:x[4].__setitem__('safe_to_act_at_B',True),
      'missing_direct_transition':lambda x:x[1]['history'][3]['witness'].__setitem__('focus',x[1]['windows'][0]),
      'crossclient_order':lambda x:x[1]['F'].__setitem__('start_ns',0),
      'forged_event':lambda x:x[1]['events_through_F'][0].__setitem__('send_event',True),
      'bool_coverage':lambda x:x[0]['subscription'].__setitem__('covered',1),
      'wrong_epoch':lambda x:x[0]['subscription'].__setitem__('epoch','foreign')}
    checks=[]
    for name,mutate in mutations.items():
        changed=copy.deepcopy(rows);mutate(changed);assert materially_changed(rows,changed)
        try:analyze(changed);rejected=False
        except(ValueError,KeyError,TypeError):rejected=True
        checks.append({'name':name,'effective_canonical_json':True,'rejected':rejected})
    assert all(c['rejected']for c in checks)
    result.update(status='POSTRUN_SAVED_NATIVE_FOCUS_SUPPORT_SCOPED',first_formal_audit_status=first['status'],
                  original_auditor_repaired=False,raw_sha256=digest,controls=checks,native_producer_invocations=0,
                  formal_auditor_invocations=0,scope='closed-world two-window focus source only; no action permission')
    with(root/'validation/AUDIT_SAVED_V2.json').open('x')as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result))
if __name__=='__main__':main()
