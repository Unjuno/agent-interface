import hashlib,json,pathlib,sys,subprocess
root=pathlib.Path(sys.argv[1]); repo=pathlib.Path(sys.argv[2])
sys.path.insert(0,str(repo))
from runtime.guarded_x11_v1.calc_profile_v1 import verify_saved_fods_bytes
samples=json.loads((root/'r84-a8/artifact-stability-samples.json').read_bytes())
offsets=[s['offset_ms'] for s in samples]
sample_rows=[]
for s in samples:
 raw=(root/'r84-a8'/s['raw_path']).read_bytes()
 parsed=verify_saved_fods_bytes(raw)
 sample_rows.append({'offset_ms':s['offset_ms'],'sha256':hashlib.sha256(raw).hexdigest(),
  'bytes':len(raw),'record_sha_matches':hashlib.sha256(raw).hexdigest()==s['sha256'],
  'verifier_reproduced':parsed==s['verification'],'status':parsed.get('status'),
  'task_success':parsed.get('task_success'),'stable_during_read':s['stable_during_read'],
  'mtime_ns':s['fd_before']['mtime_ns'],'inode':s['fd_before']['inode']})
path_after=json.loads((root/'r84-a8/artifact-path-read-after-samples.json').read_bytes())
close_snapshot=json.loads((root/'r84-a8/artifact-after-close.json').read_bytes())
close=json.loads((root/'r84-a8/close.json').read_bytes())
parent=json.loads((root/'r84-a8/verify-task.json').read_bytes())
container=json.loads((root/'r84-a8/docker-exit-code.json').read_bytes())
compiled=json.loads((root/'r84-a8/compiled-result.json').read_bytes())
life=close['calc_target_lifecycle'][0]
old=repo/'research/integration/issue57_ocr_frontier_replication_20261103_r78_r83/r80-a6'
old_before=json.loads((old/'artifact-read-before-close.json').read_bytes())
old_compiled=json.loads((old/'compiled-result.json').read_bytes())
old_artifact=next((old/'server-output').glob('*/task-artifact.fods'))
old_after=old_artifact.read_bytes()
old_after_parsed=verify_saved_fods_bytes(old_after)
first=samples[0]
freeze=json.loads((root/'source-freeze.json').read_bytes())
head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
checks={
 'head_matches_frozen_base':freeze['base_commit']==head,
 'sample_offsets_exact':offsets==[0,100,250,500,1000],
 'all_samples_same_sha':len({s['sha256'] for s in samples})==1,
 'all_samples_stable':all(s['stable_during_read'] for s in samples),
 'all_samples_verified':all(s['verification'].get('status')=='verified' and s['verification'].get('task_success') is True for s in samples),
 'preclose_snapshot_differs_from_blank':first['sha256']!=compiled['task_artifact_admission']['blank_sha256'],
 'path_verifier_after_samples_verified':path_after.get('status')=='verified',
 'after_close_snapshot_verified':close_snapshot['verification'].get('status')=='verified',
 'same_sha_after_close':close_snapshot['sha256']==first['sha256'],
 'close_release_confirmed':close.get('release_confirmed') is True,
 'release_empty':close.get('release',{}).get('keys_down')==[] and close.get('release',{}).get('buttons_down')==[],
 'owner_exit_zero':close.get('owner_process_exitcode')==0,
 'natural_target_exit_zero':life['target_process_exit_receipt'].get('verified') is True and life['target_process_exit_receipt'].get('exit_code')==0,
 'clean_exit':life['process_group_cleanup'].get('clean_exit_verified') is True,
 'parent_verifier_passed':parent.get('status')=='verified' and parent.get('task_success') is True,
 'container_exit_zero':container['exit_code']==0,
 'r80_t0_was_blank_artifact':old_before['artifact_sha256']==old_compiled['task_artifact_admission']['blank_sha256'],
 'r80_retained_afterrun_file_now_verifies':old_after_parsed.get('status')=='verified' and old_after_parsed.get('task_success') is True,
 'r80_before_after_hashes_differ':old_before['artifact_sha256']!=hashlib.sha256(old_after).hexdigest()
}
summary={'schema':'agent-interface/issue57-artifact-snapshot-diagnostic-v1',
 'attempt':'r84-a8','condition':'predicate-scoped OCR skip','diagnostic_result':'DID_NOT_REPRODUCE_R80_BLANK_PRE-CLOSE_SNAPSHOT',
 'r84_task_gate_pass':all(v for k,v in checks.items() if not k.startswith('r80_')),
 'checks':checks,'samples':sample_rows,
 'r80_contrast':{'preclose_sha256':old_before['artifact_sha256'],
   'blank_sha256':old_compiled['task_artifact_admission']['blank_sha256'],
   'retained_afterrun_sha256':hashlib.sha256(old_after).hexdigest(),
   'retained_afterrun_verification':old_after_parsed},
 'compiled_method_outcome':compiled['method_receipt'].get('outcome'),
 'compiled_method_reason':compiled['method_receipt'].get('reason'),
 'parent_task_success':parent.get('task_success'),
 'interpretation':'The r80 pre-close read was byte-identical to its blank artifact; the retained file later differs and verifies. r84 was already valid at the first immutable sample and remained byte/stat-time stable through 1000ms and after close. This shows a transient write/progression discrepancy is plausible but does not establish its cause or OCR causality.'}
(root/'analysis.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'diagnostic_result':summary['diagnostic_result'],'task_gate_pass':summary['r84_task_gate_pass'],'checks':checks,'sample_sha':[s['sha256'] for s in sample_rows]},indent=2))