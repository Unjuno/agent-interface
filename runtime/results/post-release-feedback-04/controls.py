import copy,json,shutil,subprocess,sys,tarfile,tempfile
from pathlib import Path
from verify import verify
from analyze import analyze,load
root=Path(__file__).resolve().parent;checks=[]
def need(v,m):
 if not v:raise ValueError(m)
r=subprocess.run([sys.executable,'-O',str(root/'verify.py')],capture_output=True,text=True);need(r.returncode==0,'optimized positive');checks.append({'case':'optimized_positive','returncode':r.returncode,'stdout':r.stdout.strip()})
with tempfile.TemporaryDirectory() as td:
 temp=Path(td);d=temp/'bad';d.mkdir();shutil.copyfile(root/'manifest.json',d/'manifest.json');b=bytearray((root/'raw.tar.gz').read_bytes());b[len(b)//2]^=1;(d/'raw.tar.gz').write_bytes(b)
 try:verify(d)
 except ValueError as e:checks.append({'case':'corrupt_archive','rejected':True,'reason':str(e)})
 else:raise ValueError('accepted corrupted archive')
 d2=temp/'missing';d2.mkdir();shutil.copyfile(root/'raw.tar.gz',d2/'raw.tar.gz');m=load(root/'manifest.json');m['files'].append({'path':'not-present.json','bytes':0,'sha256':'0'*64});(d2/'manifest.json').write_text(json.dumps(m))
 try:verify(d2)
 except ValueError as e:checks.append({'case':'missing_manifest_member','rejected':True,'reason':str(e)})
 else:raise ValueError('accepted missing member')
 # Archive was independently byte-checked above; extract only known regular members for data-level controls.
 extracted=temp/'raw';extracted.mkdir()
 with tarfile.open(root/'raw.tar.gz') as t:
  for member in t.getmembers():
   need(member.isfile() and not Path(member.name).is_absolute() and '..' not in Path(member.name).parts,'unsafe member');p=extracted/member.name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(t.extractfile(member).read())
 p=extracted/'post-release-feedback-04';score=p/'candidate-post/session/evaluation-at-close.json';original=score.read_bytes();v=json.loads(original);v['exact_counts']['task-6']=0;score.write_text(json.dumps(v))
 try:analyze(p)
 except ValueError as e:checks.append({'case':'wrong_independent_score','rejected':True,'reason':str(e)})
 else:raise ValueError('accepted wrong score')
 score.write_bytes(original);finish=load(p/'candidate-post/session/finish.json');i=finish['taskRows'][0]['saveAttempt'];review=p/'candidate-post/host'/f'review-{i}.json';v=load(review);v['images'][0]['sha256']='0'*64;review.write_text(json.dumps(v))
 try:analyze(p)
 except ValueError as e:checks.append({'case':'wrong_review_image','rejected':True,'reason':str(e)})
 else:raise ValueError('accepted wrong reviewed image')
(root/'verification-controls.json').write_text(json.dumps({'status':'PASS','controls':checks,'scope':'Verifier countercontrols only; no new application allocation or input.'},indent=2)+'\n');print(json.dumps(checks))
