import hashlib,json,tarfile,tempfile
from pathlib import Path
from audit import audit,require
root=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
claim=json.loads((root/'result.json').read_text())
for file,key in [('raw.tar.gz','archive_sha256'),('audit.py','auditor_sha256'),('timing_reader.py','reader_sha256')]:require(sha(root/file)==claim[key],'identity '+file)
manifest=json.loads((root/'raw-manifest.json').read_text())
with tempfile.TemporaryDirectory(prefix='activation-verify-') as temp:
 with tarfile.open(root/'raw.tar.gz') as tar:
  require({m.name for m in tar.getmembers() if m.isfile()}=={'trial/'+n for n in manifest},'exact members')
  tar.extractall(temp,filter='data')
 trial=Path(temp)/'trial'
 for name,record in manifest.items():require(sha(trial/name)==record['sha256'] and (trial/name).stat().st_size==record['bytes'],'member '+name)
 actual=audit(trial/'primary');require(all(actual[k]==claim[k] for k in actual),'published claims')
 construction=trial/'construction'
 for trial_number in [1,2]:
  freeze=json.loads((construction/f'FREEZE-live-0{trial_number}.json').read_text())
  for name,digest in freeze['files'].items():
   if name.startswith('runtime/'):
    path=trial/'sources'/Path(name).name
   else:
    filename=Path(name).name
    path=construction/(filename.replace('.py','-live-01.py') if trial_number==1 else filename)
   require(sha(path)==digest,'construction frozen '+name)
 def read(p):return json.loads(p.read_text())
 first=construction/'live-01'
 require(read(first/'activation.json')['status']=='refused' and read(first/'independent-effect.json')['A_text']=='zz','failed preparation retained')
 second=construction/'live-02'
 require(read(second/'result.json')['status']=='execution_failed' and read(second/'activation.json')['status']=='completed','construction stop/activate')
 require(read(second/'before-review-control.json')['error']=='WINDOW_REVIEW_REQUIRED' and read(second/'before-review-control.json')['input_dispatched'] is False,'review gate')
 require(read(second/'after-review-control.json')['status']=='refused' and read(second/'after-review-control.json')['input_dispatched'] is False,'old alias revoked')
 require(read(second/'resumed.json')['status']=='completed' and read(second/'independent-effect.json')['A_text']=='z' and read(second/'independent-effect.json')['B_text']=='','construction effects')
 require([read(construction/n/'result.json')['status'] for n in ['native','native-02','native-03']]==['FAIL','FAIL','PASS'],'all native invocations retained')
print('PASS: frozen primary self-use, exact images/reviews, explicit activation lineage, independent effects, construction controls and retained failures. No speed/token/adoption claim.')
