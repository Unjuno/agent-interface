import hashlib,json,pathlib,sys
root=pathlib.Path(__file__).resolve().parent
freeze=json.loads((root/'FREEZE.json').read_text(encoding='utf-8-sig')); errors=[]
def check(v,m):
    if not v: errors.append(m)
for name,src in freeze['sources'].items():
    b=(root/name).read_bytes(); oid=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
    check(len(b)==src['bytes'],f'{name}: length mismatch'); check(hashlib.sha256(b).hexdigest()==src['sha256'],f'{name}: sha mismatch'); check(oid==src['git_blob'],f'{name}: git blob mismatch')
check(hashlib.sha256((root/'test_a14_pending_ammo_staleness.py').read_bytes()).hexdigest()==freeze['test_sha256'],'test freeze mismatch')
check(hashlib.sha256((root/'Containerfile').read_bytes()).hexdigest()==freeze['containerfile_sha256'],'Containerfile freeze mismatch')
raw=(root/'results/wslc.stdout.txt').read_text(encoding='utf-8-sig'); check((root/'results/exit.txt').read_text().strip()=='0','WSLc nonzero exit'); check('Ran 2 tests' in raw and raw.rstrip().endswith('OK'),'successful 2-test transcript missing')
records=json.loads((root/'results/result.json').read_text(encoding='utf-8-sig'))
for key,ammo,status,reason in [('stale',4,'REJECTED_ACTION_NOT_CURRENT','ammo_minimum_failed'),('control',6,'READY_FOR_FRESH_EXECUTOR_ADMISSION','all_authored_observable_predicates_hold')]:
    row=records[key]; check(row['prompt_ammo']==6 and row['current_ammo_after_pending_turn']==ammo and row['current_sequence']==11,f'{key}: wrong prompt/current binding'); check(row['status']==status and row['reason']==reason,f'{key}: wrong decision'); check(row['answer_eligible'] is True,f'{key}: result not eligible'); check(row['executor_admission'] is None and row['input_authority_admitted'] is False,f'{key}: unexpected authority')
if errors: print('\n'.join(errors)); sys.exit(1)
print('AUDIT_OK: frozen current-main blobs and hashes, one WSLc transcript/exit, changed-ammo rejection and unchanged control scope verified')
