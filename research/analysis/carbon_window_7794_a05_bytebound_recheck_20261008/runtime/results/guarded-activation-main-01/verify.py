import hashlib,json,tarfile,tempfile
from pathlib import Path
root=Path(__file__).resolve().parent
def require(value,message):
 if not value:raise ValueError(message)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
claim=read(root/'result.json');manifest=read(root/'raw-manifest.json')
require(sha(root/'raw.tar.gz')==claim['archive_sha256'],'archive')
with tempfile.TemporaryDirectory(prefix='activation-main-audit-') as temp:
 with tarfile.open(root/'raw.tar.gz') as tar:
  require({m.name for m in tar.getmembers()}=={'trial/'+n for n in manifest},'members');tar.extractall(temp,filter='data')
 trial=Path(temp)/'trial';case=trial/'results-local/guarded-activation-main-01/live-main-01'
 for name,r in manifest.items():require(sha(trial/name)==r['sha256'] and (trial/name).stat().st_size==r['bytes'],'member '+name)
 for name,sha256 in read(trial/'results-local/guarded-activation-main-01/FREEZE.json')['files'].items():require(sha(trial/name)==sha256,'frozen source')
 events=[json.loads(l) for l in (case/'fixture/events.jsonl').read_text().splitlines()]
 require([(e['role'],e['char']) for e in events if e['kind']=='key']==[('A','z')],'independent effects')
 require(sum(e['kind']=='focus_transfer' for e in events)==1,'exposure')
 require(read(case/'result.json')['status']=='execution_failed' and read(case/'result.json')['execution']['failed_op']==5,'initial stop')
 activation=read(case/'activation.json');require(activation['status']=='completed' and activation['execution']['program_emissions']==0,'activation')
 require(activation['execution']['activations'][0]['visual_confirmation'] is False,'not semantic confirmation')
 require(read(case/'before-review-control.json')['error']=='WINDOW_REVIEW_REQUIRED' and read(case/'before-review-control.json')['input_dispatched'] is False,'review gate')
 require(read(case/'review.json')['status']=='reviewed' and read(case/'review.json')['binding_revision']==1,'review')
 require(read(case/'after-review-control.json')['status']=='refused' and read(case/'after-review-control.json')['input_dispatched'] is False,'old alias')
 require(read(case/'resumed.json')['status']=='completed','new input')
 for name in ['result','activation','resumed']:
  releases=read(case/(name+'.json'))['execution']['releases'];require(releases and all(r['verified'] and not r['keys_down'] and not r['buttons_down'] for r in releases),'neutral release')
 effect=read(case/'independent-effect.json');require(effect['events']==events and effect['A_text']=='z' and effect['B_text']=='','effect reconstruction')
 require(all(type(p['returncode']) is int for p in read(case/'cleanup.json')),'cleanup terminal')
 require(read(trial/'results-local/guarded-activation-main-01/red.json')['exit_code']!=0,'RED retained')
 require(read(trial/'results-local/guarded-activation-main-01/native/result.json')['status']=='PASS','native suites')
print('PASS: main-specific frozen sources, real focus transfer, activation/review/new input, stale-alias controls, neutral release and independent app effects.')
