"""One-shot 30-cycle probe of per-key admission/up occupancy bounds."""
import json, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
LIVE=ROOT/'research'/'live_control'
sys.path.insert(0,str(LIVE))
import test_executor_owner_cancel_cause_v1 as integration
from lease_release_v1 import Lease

rows=[]
for trial in range(30):
    owner=displays=constants=saved=None
    row={'trial':trial,'source_head':'99b7d130742b4e884709a862bc074d15e6b42ac9'}
    try:
        owner,displays,constants,_dequeued,_slot,_thread,saved=integration.make_owner()
        lease=Lease(time.perf_counter_ns()+5_000_000_000)
        lease.expected_focus=41
        admission=owner.call('down',lease,'W')
        release=owner.call('up',lease,'W')
        state=owner.call('input_state')
        row.update({
            'owner_id':owner.owner_id,
            'admission':admission,
            'release':release,
            'state_after':state,
            'display_events':displays[0].events,
            'fake_keys_down_after':sorted(displays[0].down),
            'owner_records':owner.records,
        })
        if type(admission) is dict and type(release) is dict:
            row['hold_lower_bound_ns']=max(0,release['release_call_started_ns']-admission['input_ack_ns'])
            row['hold_upper_bound_ns']=release['release_call_returned_ns']-admission['admitted_ns']
            row['bound_width_ns']=row['hold_upper_bound_ns']-row['hold_lower_bound_ns']
    except Exception as exc:
        row['error']={'type':type(exc).__name__,'message':str(exc)}
    finally:
        if owner is not None:
            try: owner.close()
            except Exception as exc: row['close_error']={'type':type(exc).__name__,'message':str(exc)}
        sys.modules.pop('input_transition_owner_v4',None)
        sys.modules.pop('input_owner_v12',None)
        if saved is not None:
            sys.modules.pop('owner_under_test',None)
            for name,module in saved.items():
                if module is None: sys.modules.pop(name,None)
                else: sys.modules[name]=module
    rows.append(row)
result={
 'run_id':'MAP01-V39-KEY-HOLD-BOUNDS-CONFIRM-30-MAIN27F-PR99B7-20261004',
 'base_commit':'27f6e9ff02f21afbe56579b72063c19b2dbd74bb',
 'pr_head':'99b7d130742b4e884709a862bc074d15e6b42ac9',
 'scope':'exact InputTransitionOwnerV4 + InputOwnerV12 down/up receipts; fake Xlib, no app/game',
 'planned_trials':30,'rows':rows,
}
(ROOT/'RAW-30.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({'run_id':result['run_id'],'trials':len(rows),'error_trials':sum('error'in r for r in rows),'raw_file':'RAW-30.json'},sort_keys=True))


