import hashlib,json,platform,sys
from pathlib import Path
root=Path(__file__).resolve().parent
files=[
 'run_hold_bound_30.py','audit_hold_bound_30.py','freeze_hold_bound.py',
 'research/live_control/executor_v3.py','research/live_control/executor_v5.py',
 'research/live_control/executor_v11.py','research/live_control/executor_v12.py',
 'research/live_control/lease.py','research/live_control/lease_cause_v1.py',
 'research/live_control/lease_cause_v2.py','research/live_control/lease_release_v1.py',
 'research/live_control/input_owner_v12.py','research/live_control/input_transition_owner_v4.py',
 'research/live_control/test_executor_owner_cancel_cause_v1.py']
freeze={
 'run_id':'MAP01-V39-KEY-HOLD-BOUNDS-CONFIRM-30-MAIN27F-PR99B7-20261004',
 'frozen_at_utc':'2026-10-04T04:56:54Z',
 'base_commit':'27f6e9ff02f21afbe56579b72063c19b2dbd74bb',
 'pr_head':'99b7d130742b4e884709a862bc074d15e6b42ac9',
 'hypothesis':'For each normal explicit key-up, admission and release call brackets bound the synthetic key-held interval.',
 'trial_design':'One batch of 30 fresh owner/lease instances; one W down, one W up, then one owner input_state sample per trial. Earlier one-cycle pilot used prior main/PR source identities and is excluded.',
 'decision':'PASS iff all 30 rows have matching W admission/up receipts, matching lease token and owner id, ordinary valid release, monotonic timestamps, verified-empty post-up state, fake KeyPress/KeyRelease pair, frozen source hashes, and recomputed finite lower<=upper interval; otherwise FAIL/HOLD. No retries.',
 'bounds_ns':{
  'lower':'max(0, release_call_started_ns - input_ack_ns)',
  'upper':'release_call_returned_ns - admitted_ns',
  'justification':'XTest down request is issued after admitted_ns and synchronized before input_ack_ns; XTest up is issued after release_call_started_ns and synchronized before release_call_returned_ns.'},
 'scope':'Construction measurement only: current-main Executor stack as import context, current PR InputTransitionOwnerV4/InputOwnerV12 down/up API with in-memory fake Xlib; no application, game, model, GUI, or allocation.',
 'pilot_excluded':True,
 'runtime':{'python':sys.version,'platform':platform.platform()},
 'source_sha256':{name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in files},
}
(root/'PRE-RUN.json').write_text(json.dumps(freeze,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({'run_id':freeze['run_id'],'frozen_at_utc':freeze['frozen_at_utc'],'source_count':len(files),'python':platform.python_version(),'decision':freeze['decision']},sort_keys=True))


