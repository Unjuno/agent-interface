import hashlib,json,pathlib
root=pathlib.Path.cwd(); p=root/'research/doom/results/absolute_pair_useful_effect_audit_20261005_a02'; source=root/'research/doom/absolute_pair_59_4d74_20261004'
f=json.loads((p/'FREEZE.json').read_text()); a=json.loads((p/'AUDIT.json').read_text()); run=json.loads((p/'RUN_RESULT.json').read_text()); a01=json.loads((root/'research/doom/results/absolute_pair_useful_effect_audit_20261005/AUDIT.json').read_text())
checks={}
checks['all_48_frozen_inputs_match']=len(f['inputs'])==48 and all((source/k).is_file() and hashlib.sha256((source/k).read_bytes()).hexdigest()==v for k,v in f['inputs'].items())
checks['auditor_hash_matches']=hashlib.sha256((root/f['auditor_path']).read_bytes()).hexdigest()==f['auditor_sha256']
checks['exact_pinned_networkless_wslc']=f['image']=='sha256:94014a0f7757b46b7c3ae83f430ad973ae6abe1722937bdc6d060139aaeb6378' and f['argv'][f['argv'].index('--network')+1]=='none' and f['argv'][f['argv'].index('--pull')+1]=='never'
checks['wslc_exit_zero']=run['exit_code']==0 and run['timed_out'] is False
checks['independent_audit_passes']=a['audit']=='PASS_AUDIT_ZERO_OBSERVED_SCORE_PROGRESS' and a['checks']['errors']==[] and a['checks']['cells']==6 and a['checks']['total_window_samples']==111 and a['checks']['release_receipts_joined']==6
checks['both_arms_zero_progress_and_safety']=all(a['arms'][arm]['cells_with_positive_progress_sample']==0 and a['arms'][arm]['cells_with_negative_safety_sample']==0 for arm in ('coast','pulse'))
checks['first_audit_failure_preserved']=a01['audit']=='FAIL' and any(e.endswith(':final_score_mismatch') for e in a01['checks']['errors'])
checks['swap_warning_retained']='Memory limited without swap' in (p/'WSLC_STDERR.txt').read_text(errors='replace')
result={'verification':'PASS' if all(checks.values()) else 'FAIL','checks':checks}
(p/'VERIFY.json').write_text(json.dumps(result,indent=2)+'\n')
files=sorted(x for x in p.iterdir() if x.is_file() and x.name!='SHA256SUMS')
(p/'SHA256SUMS').write_text(''.join(hashlib.sha256(x.read_bytes()).hexdigest()+'  '+x.relative_to(root).as_posix()+'\n' for x in files))
print(json.dumps(result,indent=2))
