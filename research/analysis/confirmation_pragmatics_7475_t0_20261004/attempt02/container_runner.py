from pathlib import Path
import hashlib,json,shutil,subprocess,sys
src=Path('/src'); work=Path('/tmp/work'); out=Path('/out')
shutil.copytree(src,work,dirs_exist_ok=True)
for name in ('facts.json','answer_key.json','PREWORDING_LOCK.json','stimuli.json','candidate.py','independent_audit.py'):
 if not (src/name).is_file(): raise SystemExit(f'MISSING_SOURCE:{name}')
print('SOURCE_READONLY_MOUNT=verified-by-input-presence')
r1=subprocess.run([sys.executable,'-B','candidate.py'],cwd=work,text=True,capture_output=True)
print('CANDIDATE_EXIT='+str(r1.returncode)); print(r1.stdout,end=''); print(r1.stderr,end='',file=sys.stderr)
if r1.returncode: raise SystemExit(r1.returncode)
r2=subprocess.run([sys.executable,'-B','independent_audit.py'],cwd=work,text=True,capture_output=True)
print('AUDITOR_EXIT='+str(r2.returncode)); print(r2.stdout,end=''); print(r2.stderr,end='',file=sys.stderr)
if r2.returncode: raise SystemExit(r2.returncode)
for n in ('candidate_raw.json','audit_result.json'):
 shutil.copyfile(work/n,out/n)
print('OUTPUTS_WRITTEN=/out/candidate_raw.json,/out/audit_result.json')
