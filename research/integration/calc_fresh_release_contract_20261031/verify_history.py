"""Crosscheck archived Calc runs and exact scope of successor runner changes."""
from pathlib import Path
from zipfile import ZipFile
import difflib,hashlib,json
here=Path(__file__).resolve().parent
source=here.parent/'wslc_calc_persistent_grounding_comparison_20261031'
expected='beb497492a564e8a58b67b2c8bd0034c9f4cce9214b54fc76e8ff52a18fb6f0c'
original=None; rows=[]
for arm in ('gg01','gg02','gg03','gg04'):
 with ZipFile(source/(arm+'.zip')) as z:
  runner=z.read('runner.py'); assert hashlib.sha256(runner).hexdigest()==expected
  if original is None:original=runner.decode('utf-8-sig')
  result=json.loads(z.read('output/result.json'));route=result['route'];receipts=[]
  if route=='fresh':
   for name in ('fresh-entry.json','fresh-save.json'):
    row=json.loads(z.read('output/'+name));releases=row['execution']['releases'];assert row['status']=='completed' and releases and all(x['verified'] is True and x['keys_down']==[] and x['buttons_down']==[] for x in releases);receipts.append(len(releases))
  else:
   transitions=result['method']['method_receipt']['transitions'];assert len(transitions)==2 and all(t['release_verified'] is True for t in transitions);receipts=[t['release_verified'] for t in transitions]
  rows.append({'arm':arm,'route':route,'release_receipts':receipts})
modified=(here/'runner-successor.py').read_text(encoding='utf-8-sig')
diff=list(difflib.unified_diff(original.splitlines(),modified.splitlines(),lineterm=''));removed=[x for x in diff if x.startswith('-') and not x.startswith('---')];added=[x for x in diff if x.startswith('+') and not x.startswith('+++')]
assert len(removed)==len(added)==2 and all('fresh ' in x and 'releases' in x for x in removed+added)
print(json.dumps({'status':'audited','historical_runner_sha256':expected,'changed_lines':len(added),'arms':rows},indent=2))
