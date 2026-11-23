#!/usr/bin/env python3
import json
from pathlib import Path
p=Path(__file__).resolve().parent/'runs/optimized-01'
r=json.loads((p/'result.json').read_text())
def need(ok,msg):
    if not ok: raise RuntimeError(msg)
need((p/'exit-code.txt').read_text().strip()=='0','R07 unittest not successful')
need(r['status']=='OBSERVED_SCOPED_XVFB_STANDARD_CALLER_CANCEL_CLEANUP_UNKNOWN','R07 scope status changed')
need(r['cancel']['owner_client_disconnect']['status']=='disconnected','R07 disconnect absent')
need(r['cancel']['owner_release_attempt']['status']=='readback_verified','R07 verified release missing')
need(r['independent_release_readback']['neutral'] is True,'R07 independent readback not neutral')
need(r['independent_task_oracle']['task_success'] is False,'R07 old-task failure missing')
need(r['independent_task_oracle']['measurements']['initial_effect_count']==[1],'R07 initial count changed')
need(r['independent_task_oracle']['measurements']['final_effect_count']==[25],'R07 final count changed')
need(r['late_request_horizon_readback']['late_keypress_a_observed'] is True,'R07 delayed A evidence missing')
need(r['fresh_session_recovery']['task_oracle']['task_success'] is True,'R07 fresh task did not pass')
need(r['fresh_session_recovery']['task_oracle']['old_unknown_fence_preserved'] is True,'R07 old UNKNOWN fence not preserved')
need(r['fresh_session_recovery']['late_old_keypress_after_new_session'] is False,'R07 old input contaminated new task')
need(r['cancel']['release_confirmed'] is False and r['cancel']['task_success'] is False,'R07 public cancellation incorrectly claims success')
need(all(v is False for v in r['final_cleanup']['keys_down'].values()),'R07 final cleanup not all-up')
print(json.dumps({'status':'SCOPED_DIAGNOSTIC_CLASSIFIED_NOT_PRODUCT_PASS','release_ms':r['cancel']['owner_release_attempt']['elapsed_ms'],'release_readback_neutral':True,'old_effect_count':'1 -> 25','old_task_success':False,'late_a':True,'fresh_task_success':True,'old_fence_unknown':True,'final_cleanup_all_up':True},indent=2))