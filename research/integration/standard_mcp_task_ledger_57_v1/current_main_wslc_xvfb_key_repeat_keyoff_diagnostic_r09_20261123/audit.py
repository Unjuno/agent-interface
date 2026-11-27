#!/usr/bin/env python3
import gzip, json
from pathlib import Path
root=Path(__file__).resolve().parent/'runs'
def need(ok,msg):
    if not ok: raise RuntimeError(msg)
def load(m): return json.loads((root/m/'result.json').read_text())
def log_text(m):
    with gzip.open(root/m/'test.log.gz','rt',encoding='utf-8',errors='replace') as stream: return stream.read()
normal=load('normal'); opt=load('optimized')
need((root/'normal/exit-code.txt').read_text().strip()=='0','normal unittest not passing')
need('OK' in log_text('normal'),'normal unittest log not OK')
need(normal['status']=='OBSERVED_SCOPED_XVFB_STANDARD_CALLER_CANCEL_CLEANUP_UNKNOWN','normal result status mismatch')
need(normal['independent_task_oracle']['task_success'] is False,'normal old task oracle did not fail')
need(normal['independent_task_oracle']['measurements']['final_effect_count']==[28],'normal effect count mismatch')
need(normal['independent_release_readback']['neutral'] is True,'normal release readback not neutral')
need(normal['fresh_session_recovery']['task_oracle']['task_success'] is True,'normal fresh task did not pass')
need(normal['fresh_session_recovery']['task_oracle']['checks']['old_unknown_fence_preserved'] is True,'normal old fence not preserved')
need(all(v is False for v in normal['final_cleanup']['keys_down'].values()),'normal cleanup not all-up')
need((root/'optimized/exit-code.txt').read_text().strip()=='1','optimized failure exit missing')
need(opt['status']=='FAIL','optimized structured failure missing')
need(opt['cancel']['owner_client_disconnect']['status']=='disconnected','optimized disconnect missing')
need(opt['cancel']['owner_release_attempt']['status']=='unknown','optimized release unknown missing')
need(opt['independent_release_readback']['neutral'] is False and opt['independent_release_readback']['keys_down']['a'] is True,'optimized A-down readback missing')
need(all(v is False for v in opt['final_cleanup']['keys_down'].values()),'optimized final cleanup not all-up')
keyboard=json.loads((root/'normal/keyboard-control.json').read_text())
need(keyboard['global_auto_repeat']==1 and keyboard['per_key_repeat_enabled'] is False,'normal keyboard setting mismatch')
keyboard_opt=json.loads((root/'optimized/keyboard-control.json').read_text())
need(keyboard_opt['global_auto_repeat']==1 and keyboard_opt['per_key_repeat_enabled'] is False,'optimized keyboard setting mismatch')
print(json.dumps({'status':'SCOPED_DIAGNOSTIC_CLASSIFIED_NOT_PRODUCT_PASS','normal_effect_count':[28],'normal_old_task_success':False,'normal_release_neutral':True,'normal_fresh_task_success':True,'optimized_release':'unknown','optimized_final_cleanup_all_up':True,'repeat_setting_verified':True},indent=2))
