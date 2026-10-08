import hashlib,json,tarfile,tempfile
from pathlib import Path
root=Path(__file__).resolve().parent
def require(value,message):
 if not value:raise ValueError(message)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((root/'raw-manifest.json').read_text())
require(sha(root/'raw.tar.gz')==json.loads((root/'result.json').read_text())['archive_sha256'],'archive')
with tempfile.TemporaryDirectory(prefix='focus-main-audit-') as temp:
 with tarfile.open(root/'raw.tar.gz') as tar:
  require({m.name for m in tar.getmembers()}=={'trial/'+n for n in manifest},'members');tar.extractall(temp,filter='data')
 trial=Path(temp)/'trial'
 for name,r in manifest.items():require(sha(trial/name)==r['sha256'] and (trial/name).stat().st_size==r['bytes'],'member '+name)
 freeze=json.loads((trial/'results-local/focus-transfer-01/FREEZE.json').read_text())
 for name,digest in freeze['files'].items():require(sha(trial/name)==digest,'frozen source '+name)
 for name,keys,status in [('corrected-main-01',[],'execution_failed'),('stable-main-01',[('A','z')],'completed')]:
  case=trial/'results-local/focus-transfer-01'/name
  events=[json.loads(l) for l in (case/'fixture/events.jsonl').read_text().splitlines()]
  require([(e['role'],e['char']) for e in events if e['kind']=='key']==keys,'key effects')
  require(sum(e['kind']=='focus_transfer' for e in events)==(1 if name.startswith('corrected') else 0),'transfer exposure')
  result=json.loads((case/'result.json').read_text());require(result['status']==status,'status')
  require(all(r['verified'] and not r['keys_down'] and not r['buttons_down'] for r in result['execution']['releases']),'neutral release')
  if status=='execution_failed':require(result['execution']['failed_op']==5 and 'outside guarded target before key press' in result['execution']['error'],'focus failure')
 require(json.loads((trial/'results-local/guarded-focus-stop-main-01/native/result.json').read_text())['status']=='PASS','native checks')
print('PASS: main-specific frozen sources, disturbance stops, stable input works, verified neutral releases and local contract checks.')
