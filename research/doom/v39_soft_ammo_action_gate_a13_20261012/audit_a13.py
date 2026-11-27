import argparse, hashlib, json, pathlib, re, sys
root=pathlib.Path(__file__).resolve().parent
freeze=json.loads((root/'FREEZE.json').read_text(encoding='utf-8-sig'))
errors=[]
def check(ok,msg):
    if not ok: errors.append(msg)
for name,info in freeze['sources'].items():
    p=root/name; b=p.read_bytes()
    check(len(b)==info['bytes'],f'{name}: byte length mismatch')
    check(hashlib.sha256(b).hexdigest()==info['sha256'],f'{name}: sha256 mismatch')
    oid=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
    check(oid==info['git_blob'],f'{name}: git blob mismatch')
check(hashlib.sha256((root/'test_a13_feedback_action_gate.py').read_bytes()).hexdigest()==freeze['test_sha256'],'test sha256 mismatch')
check(hashlib.sha256((root/'Containerfile').read_bytes()).hexdigest()==freeze['containerfile_sha256'],'Containerfile sha256 mismatch')
raw=(root/'results/wslc.stdout.txt').read_text(encoding='utf-8-sig')
check((root/'results/exit.txt').read_text().strip()=='0','WSLc exit code not zero')
check('Ran 2 tests' in raw and raw.rstrip().endswith('OK'),'WSLc output missing successful 2-test summary')
check('test_soft_ammo_feedback_reaches_prompt_and_fresh_action_gate_rejects_fire' in raw,'soft feedback test missing')
check('test_matching_ammo_positive_control_reaches_executor_ready_but_not_admitted' in raw,'positive control test missing')
m=re.search(r'^A13_RESULT=(\{.*\})$',raw,re.M)
check(m is not None,'A13_RESULT line missing')
if m:
    observed=json.loads(m.group(1)); saved=json.loads((root/'results/result.json').read_text(encoding='utf-8-sig'))
    check(observed==saved,'saved result differs from stdout')
    check(observed.get('final_admission_reason')=='ammo_minimum_failed','unexpected rejection reason')
    check(observed.get('final_admission_status')=='REJECTED_ACTION_NOT_CURRENT','unexpected rejection status')
    check(observed.get('executor_admission') is None,'executor unexpectedly admitted')
    check(observed.get('input_authority_admitted') is False,'input authority unexpectedly admitted')
    check(observed.get('prompt_has_current_ammo_4') is True,'prompt ammo missing')
    check(observed.get('soft_event_summary',{}).get('grants_input_authority') is False,'soft event unexpectedly grants authority')
if errors:
    print('\n'.join(errors)); sys.exit(1)
print('AUDIT_OK: frozen source blob IDs and hashes, test/container hashes, WSLc stdout/exit, and result scope verified')
