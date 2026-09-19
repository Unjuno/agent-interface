import hashlib,json,subprocess,sys
from pathlib import Path
from native_exchange_v1 import run
p=Path('results-local/native-owner-stop-02')
before={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in p.rglob('*') if f.is_file()}
decision=json.loads((p/'request-1.json').read_text())
try:
    run(p,1,decision,timeout=0)
except FileExistsError as error:
    duplicate={'refused':True,'error':str(error)}
else:
    raise AssertionError('duplicate submission accepted')
result=subprocess.run([sys.executable,'research/live_control/run_native_calc_self_use_v1.py',
    '--app','inkscape','--out',str(p)],capture_output=True,text=True)
assert result.returncode!=0 and 'FileExistsError' in result.stderr
after={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in p.rglob('*') if f.is_file()}
assert before==after
programs=list((p/'bridge').glob('program-*.json'))
assert len(programs)==1 and not (p/'reply-1.json').exists()
row={'duplicate_submission':duplicate,'same_directory_owner_restart':{
    'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr},
    'all_existing_files_unchanged':True,'retained_native_programs':len(programs)}
(p/'control-results.json').write_text(json.dumps(row,indent=2)+'\n')
print(json.dumps(row,indent=2))
