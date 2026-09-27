import hashlib,io,json,tarfile
from pathlib import Path
from openpyxl import load_workbook
root=Path(__file__).parent
manifest=json.loads((root/'manifest.json').read_text())
with tarfile.open(root/'raw.tar.gz') as t: files={m.name:t.extractfile(m).read() for m in t.getmembers() if m.isfile()}
assert set(files)==set(manifest)
for name,sha in manifest.items():assert hashlib.sha256(files[name]).hexdigest()==sha,name
def read(name):return json.loads(files[name].decode('utf-8-sig'))
def response(trial,label):return json.loads(read(f'native-sdk-primary-{trial}/{label}-response.json')['content'][0]['text'])
assert response('06','action-6')['allocation']['returncode']==0
r='native-sdk-allocation-06/run/'
old=read(r+'source-1.json'); pending=read(r+'source-2.json'); fresh=read(r+'source-3.json')
assert pending['review_recovery']['status']=='observation_required'
assert pending['native']==old['native'] and pending['sequence']==old['sequence']
assert 'review_recovery' not in fresh and fresh['sequence']>old['sequence']
assert read(r+'request-2.json')=={'interaction':'observe','source_sequence':old['sequence']}
assert read(r+'request-4.json')['interaction']=='observe'
actions=read(r+'actions.json');assert len(actions)==2
for action in actions:
 assert action['result']['status']=='completed'
 releases=action['result']['execution']['releases'];assert releases
 assert all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in releases)
assert read(r+'evaluation.json')['success'] is True
book=load_workbook(io.BytesIO(files[r+'sheet.xlsx']),data_only=True)
assert [book.active['A1'].value,book.active['A2'].value]==[384,897];book.close()
assert read(r+'cleanup-report.json')['tracked_processes_terminal'] is True

assert response('06','action-1')['continuation']['status']=='observation_required'
assert response('06','action-5')['outcome_summary']['evaluation_success'] is True
assert read('native-sdk-primary-06/PRIMARY_REVIEW.json')['oracle_not_yet_read'] is True
assert read('native-sdk-primary-06/plan.json')['source']=='8ea0f7cff893625652024ef9a48b8df2c5c69bec'
print(f'PASS {len(files)} files; integrated-main recovery retained; saved cells correct')
