#!/usr/bin/env python3
import copy,json,pathlib
from audit import audit_rows
base=json.loads(pathlib.Path('construction-04/ROWS.json').read_text()); out=[]
def chk(name,fn):
    x=copy.deepcopy(base); fn(x); rejected=bool(audit_rows(x,1)['errors']); out.append({'name':name,'rejected':rejected})
chk('drop_row',lambda x:x.pop())
chk('duplicate_row',lambda x:x.append(copy.deepcopy(x[0])))
chk('replacement_pid_same',lambda x: next(r for r in x if r['policy']=='BOUNDED_SKEW' and r['schedule']=='WINDOW_REPLACEMENT')['raw'].__setitem__('app_pid_current',next(r for r in x if r['policy']=='BOUNDED_SKEW' and r['schedule']=='WINDOW_REPLACEMENT')['raw']['app_pid_initial']))
chk('replacement_xid_changed',lambda x: next(r for r in x if r['policy']=='BOUNDED_SKEW' and r['schedule']=='WINDOW_REPLACEMENT')['raw'].__setitem__('xid_current',999))
chk('replacement_join_false',lambda x: next(r for r in x if r['policy']=='BOUNDED_SKEW' and r['schedule']=='WINDOW_REPLACEMENT').__setitem__('join',False))
chk('replacement_oracle_true',lambda x: next(r for r in x if r['policy']=='BOUNDED_SKEW' and r['schedule']=='WINDOW_REPLACEMENT').__setitem__('oracle_join',True))
chk('focus_unsafe_join',lambda x: next(r for r in x if r['policy']=='BOUNDED_SKEW' and r['schedule']=='FOCUS_CHANGE').__setitem__('join',True))
chk('identity_generation_current',lambda x: next(r for r in x if r['policy']=='BOUNDED_SKEW' and r['schedule']=='IDENTITY_MISMATCH')['fields']['image'].__setitem__('generation',1))
chk('effect_missing',lambda x: next(r for r in x if r['policy']=='BOUNDED_SKEW' and r['schedule']=='STABLE')['effect_score'].__setitem__('status','ABSENT'))
chk('effect_on_refusal',lambda x: next(r for r in x if r['policy']=='STRICT_ANCHOR' and r['schedule']=='STABLE')['effect_score'].__setitem__('status','EXACT'))
chk('release_nonempty',lambda x: x[0]['release'].__setitem__('keys_down_after',[38]))
chk('image_hash',lambda x: x[0]['fields']['image'].__setitem__('sha256','0'*64))
chk('xvfb_exit',lambda x: x[0]['process_exits'].__setitem__('xvfb',9))
res={'controls':out,'all_rejected':all(i['rejected'] for i in out)}; pathlib.Path('CONTROLS.json').write_text(json.dumps(res,indent=2,sort_keys=True)+'\n'); print(json.dumps(res,sort_keys=True)); raise SystemExit(0 if res['all_rejected'] else 1)
