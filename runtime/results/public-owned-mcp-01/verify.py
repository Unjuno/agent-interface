from pathlib import Path
import hashlib,io,json,tarfile
from openpyxl import load_workbook
root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text())
with tarfile.open(root/'raw.tar.gz','r:gz') as tar:
 members={m.name:m for m in tar.getmembers()}
 assert set(members)==set(manifest['files'])
 def read(n):return tar.extractfile(members[n]).read()
 def data(n):return json.loads(read(n))
 for n,h in manifest['files'].items():assert hashlib.sha256(read(n)).hexdigest()==h,n
 for run,expected,last in [('public-owned-calc-primary-01',[None,None],6),('public-owned-calc-primary-02',[597,624],9)]:
  prefix='results-local/'+run+'/'
  book=load_workbook(io.BytesIO(read(prefix+'saved.xlsx')),data_only=True)
  actual=[book.active['A1'].value,book.active['A2'].value];book.close()
  assert actual==expected
  evaluation=data(prefix+'evaluation.json')
  assert evaluation['actual']==actual and evaluation['success']==(run.endswith('02'))
  initial=data(prefix+'initial-metadata.json');sid=initial['session']['session_id']
  for n in range(1,last+1):assert data(prefix+f'action-{n}-metadata.json')['session']['session_id']==sid
  close=data(prefix+f'action-{last}-metadata.json')
  assert close['status']=='closed' and close['connection_close_attempted']
  assert close['release']['verified'] and close['release']['keys_down']==close['release']['buttons_down']==[]
  assert data(prefix+'terminal-result.json')['runner_exit_code']==0
  assert data(prefix+'fixture-cleanup.json')['session_close_returned']
 p='results-local/public-owned-calc-primary-01/'
 assert data(p+'action-3-metadata.json')['outcome_summary']['execution_status']=='execution_failed'
 assert data(p+'action-5-metadata.json')['outcome_summary']['execution_status']=='refused'
 p='results-local/public-owned-calc-primary-02/'
 for n in (1,5):
  result=data(p+f'action-{n}-metadata.json')['outcome_summary']
  assert result['execution_status']=='completed' and result['input_release_verified']
 for n,revision in ((3,2),(7,3)):
  result=data(p+f'action-{n}-metadata.json')
  assert result['status']=='target_reviewed' and result['binding_revision']==revision
  assert result['input_dispatched'] is False and result['authority_granted'] is False
 assert data('results-local/public-owned-target-check-01/result.json')['status']=='PASS'
 print('PASS:',len(members),'retained files; failed and successful saved-file outcomes, same-session review/release/close. No performance inference.')