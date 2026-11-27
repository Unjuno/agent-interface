import hashlib,json,pathlib,sys,re
root=pathlib.Path(__file__).resolve().parent;freeze=json.loads((root/'FREEZE.json').read_text(encoding='utf-8-sig'));errors=[]
def check(v,m):
 if not v:errors.append(m)
for name,s in freeze['sources'].items():
 b=(root/name).read_bytes();oid=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();check(len(b)==s['bytes'],name+' length');check(hashlib.sha256(b).hexdigest()==s['sha256'],name+' sha');check(oid==s['git_blob'],name+' blob')
check(hashlib.sha256((root/'test_a16_pending_ammo_threshold.py').read_bytes()).hexdigest()==freeze['test_sha256'],'test freeze')
check(hashlib.sha256((root/'Containerfile').read_bytes()).hexdigest()==freeze['containerfile_sha256'],'container freeze')
raw=(root/'results/wslc.stdout.txt').read_text(encoding='utf-8-sig');check((root/'results/exit.txt').read_text().strip()=='0','exit code');check('Ran 2 tests' in raw and re.search(r'(?m)^OK\r?$',raw) is not None,'raw success summary')
r=json.loads((root/'results/result.json').read_text(encoding='utf-8-sig'));soft,hard=r['soft'],r['hard']
check(soft['observed_ammo']==4 and soft['soft_event_count']==1 and soft['monitor_invalidation'] is None,'soft event classification')
check(soft['turn_answer_eligible'] is True and soft['final_admission']=='REJECTED_ACTION_NOT_CURRENT' and soft['final_reason']=='ammo_minimum_failed','soft final gate')
check(hard['observed_ammo']==0 and hard['monitor_invalidation']['reason']=='ammo:below_hard_minimum','hard invalidation')
check(hard['event_order'][-3:]==['monitor_invalidation','pre_interrupt_callback','interrupt_request'],'hard interrupt ordering')
check(hard['turn_answer_eligible'] is False and hard['final_admission'] is None,'late answer invalidated')
for arm in (soft,hard):check(arm['executor_admission'] is None and arm['input_authority_admitted'] is False,'unexpected authority')
if errors:print('\n'.join(errors));sys.exit(1)
print('AUDIT_OK: frozen source blobs/hashes, test/container identity, WSLc run, soft/hard outcome distinction, interrupt order and authority limits verified')

