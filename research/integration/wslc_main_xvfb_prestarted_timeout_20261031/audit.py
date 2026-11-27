"""Check the retained unsuccessful prestarted-supervisor trial."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json
p=Path(__file__).with_name('public.zip')
assert hashlib.sha256(p.read_bytes()).hexdigest()=='0dd930d492648b9cd78e6f7c2d9fc0bc28166fbbcec72d1223bd07b0c0444183'
with ZipFile(p) as z:
 m=json.loads(z.read('manifest.json'))
 assert set(z.namelist())==set(m['files'])|{'manifest.json'}
 for n,h in m['files'].items(): assert hashlib.sha256(z.read(n)).hexdigest()==h,n
 run=json.loads(z.read('out/launcher.json'));r=json.loads(z.read('out/receipt.json'))
 assert run['exit_code']==1 and not run['timeout'] and r['status']=='FAIL'
 assert r['conditions']['prestarted_cancel_supervisor'] is True
 c=r['stopped_terminal']['cancellation'];o=c['result']['owner_release_attempt']
 assert c['result']['cleanup_status']=='UNKNOWN' and c['release_confirmed'] is False and c['replay_allowed'] is False
 assert o['status']=='unknown' and o['reason']=='transaction_deadline' and o['worker_retired'] is True
 assert r['server_resume']['status']=='resumed' and r['final_cleanup']['keys_down']=={'a':False,'b':False}
 assert r['synthetic_task_oracle'] is None and r.get('recovery') is None
 assert b"'unknown' != 'not_attempted'" in z.read('out/stderr.bin')
 print(json.dumps({'status':'audited','experiment':'FAIL','old_task_oracle':'not_reached','fresh_task_oracle':'not_reached','cleanup':'UNKNOWN; isolated harness ended with both keys up'},indent=2))
