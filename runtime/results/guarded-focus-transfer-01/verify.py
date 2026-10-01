"""Raw-only independent effect audit; never launches X11 or dispatches input."""
import hashlib,json,tarfile,tempfile
from pathlib import Path
root=Path(__file__).resolve().parent
def require(condition,message):
 if not condition:raise ValueError(message)
def sha(data):return hashlib.sha256(data).hexdigest()
manifest=json.loads((root/'raw-manifest.json').read_text())
claim=json.loads((root/'result.json').read_text())
require(sha((root/'raw.tar.gz').read_bytes())==claim['archive_sha256'],'archive identity')
with tempfile.TemporaryDirectory(prefix='focus-audit-') as temp:
 with tarfile.open(root/'raw.tar.gz') as tar:
  require({m.name for m in tar.getmembers()}=={'trial/'+name for name in manifest},'exact members')
  tar.extractall(temp,filter='data')
 trial=Path(temp)/'trial'
 for name,record in manifest.items():
  data=(trial/name).read_bytes();require(sha(data)==record['sha256'] and len(data)==record['bytes'],'member hash '+name)
 for case,expected,status in [('baseline-05','B','completed'),('corrected-01',None,'execution_failed'),('stable-control-01','A','completed')]:
  directory=trial/case
  events=[json.loads(line) for line in (directory/'fixture/events.jsonl').read_text().splitlines()]
  keys=[(e['role'],e['char']) for e in events if e.get('kind')=='key']
  require(keys==([] if expected is None else [(expected,'z')]),'independent key effects '+case)
  result=json.loads((directory/'result.json').read_text());require(result['status']==status,'status '+case)
  releases=result['execution']['releases']
  require(releases and all(r['verified'] and not r['keys_down'] and not r['buttons_down'] for r in releases),'neutral releases')
  if case=='corrected-01':
   require(result['execution']['failed_op']==5 and 'outside guarded target before key press' in result['execution']['error'],'focus stop')
  transfer=[e for e in events if e['kind']=='focus_transfer']
  require(len(transfer)==(0 if case=='stable-control-01' else 1),'disturbance exposure')
  if expected=='B':require(transfer[0]['monotonic_ns']<events[-1]['monotonic_ns'],'transfer before wrong input')
print('PASS: baseline sends z to B; corrected stops without keyboard input; stable control sends z to A; neutral releases retained.')
