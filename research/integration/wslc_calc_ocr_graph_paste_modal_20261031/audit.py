"""Audit private Calc clipboard-paste observation and retained modal."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json
p=Path(__file__).with_name('public.zip');assert hashlib.sha256(p.read_bytes()).hexdigest()=='a19685954ce571d564054aa849723b79498b358c183882c7383fb751a02d0b4c'
with ZipFile(p) as z:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'))
 m=j('manifest.json');assert set(z.namelist())==set(m['files'])|{'manifest.json'}
 for n,h in m['files'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
 v=j('verification.json');assert v['source_checked']==2092 and not v['source_mismatches'] and not v['candidate_mismatches'] and v['wslc_list_exit']==0 and v['running_list_empty']
 pre=j('source-precheck.json');assert pre['source_manifest_sha256']==hashlib.sha256(z.read('source-hashes.json')).hexdigest()
 c=j('f09/conditions.json');launch=j('f09/launcher-result.json');r=j('f09/output/result.json');trace=j('f09/output/trace.json');ocr=j('f09/output/ocr.json')
 assert c['allocation']=='f09' and launch['exit_code']==0 and not launch['timeout']
 for n,h in c['candidate'].items():assert hashlib.sha256(z.read('candidate/'+n)).hexdigest()==h,n
 for n in ['calc_ocr_pair_cue_v1.py','calc_ocr_graph_perception_v1.py']:assert z.read('candidate/research/live_control/'+n)==(Path(__file__).resolve().parents[2]/'live_control'/n).read_bytes()
 assert j('f09/output/clipboard-ready.json')['owned'] is True
 method=r['method'];assert method['outcome']=='SAFE_YIELD' and method['reason']=='effect_unavailable' and method['completed_transitions']==1 and method['pending_effect']['action']=='enter'
 assert r['close']['status']=='closed' and r['close']['release']['verified'] and not r['close']['release']['keys_down'] and not r['close']['release']['buttons_down'] and not r['keys_down'] and not r['buttons']
 assert z.read('f09/output/saved.fods')==z.read('candidate/blank.fods') and not r['saved_score']['pass_effect'] and not r['saved_score']['populated']
 deps=[j(n) for n in z.namelist() if n.startswith('f09/output/owner/') and n.endswith('-input_dependency.json')];executions=[j(n) for n in z.namelist() if n.startswith('f09/output/owner/') and n.endswith('-execution.json')];assert len(executions)==1
 ex=executions[0];assert ex['request']['action']=='enter' and ex['result']['status']=='completed' and ex['result']['execution']['emissions']==4 and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in ex['result']['execution']['releases'])
 assert {x['stage'] for x in deps}=={'before_admission','before_focus','before_key_press:CTRL','before_key_press:v'} and all(x['eligible'] and x['predicates']['cells_blank'] is True for x in deps)
 images={hashlib.sha256(z.read(n)).hexdigest():z.read(n) for n in z.namelist() if n.startswith('f09/output/owner/') and n.endswith('.png')};assert all(x['artifact_sha256'] in images for x in trace) and trace[0]['valid'] and trace[0]['blank'] and not trace[-1]['valid'] and trace[-1]['blank'] is None and trace[0]['artifact_sha256']!=trace[-1]['artifact_sha256']
 assert all(x.get('skipped')=='visually_blank' for x in ocr) and len(ocr)==len(trace)
 offline=j('f09/output/offline-modal-ocr.json');assert offline['source_sha256']==trace[-1]['artifact_sha256'] and offline['returncode']==0 and offline['mode']=='posthoc offline full screenshot' and hashlib.sha256(z.read('f09/output/offline-modal-ocr.tsv')).hexdigest()==offline['stdout_sha256']
 assert not any(n.endswith('mint-recovery_save.json') for n in z.namelist() if n.startswith('f09/output/'))
 print(json.dumps({'status':'audited','outcome':method['outcome'],'reason':method['reason'],'completed_transitions':1,'pending':'enter','neutral_release':True,'saved_file':'unchanged blank','live_ocr_calls':0,'posthoc_ocr':'retained, not used for control'},indent=2))
