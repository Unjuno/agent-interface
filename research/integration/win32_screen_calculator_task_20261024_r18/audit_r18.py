from pathlib import Path
import hashlib,json
from PIL import Image
p=Path(__file__).resolve().parent;run=p/'run'
def j(n):return json.loads((run/n).read_text(encoding='utf-8'))
def sha(x):return hashlib.sha256(x.read_bytes()).hexdigest()
conditions=json.loads((p/'conditions.json').read_text(encoding='utf-8'));obs=j('observation-parsed.json');report=obs['receipt']['report'];close=j('close.json');uia=j('uia-baseline.json')['parsed'];img=Image.open(run/'observation-image-00.png').convert('RGB')
manifest={}
for line in (p/'FROZEN_SHA256SUMS').read_text(encoding='ascii').splitlines():h,n=line.split('  ',1);manifest[n]=h
manifest_ok=all(sha(p/n)==h for n,h in manifest.items())
error=j('runner-error.json')
audit={'schema':'win32-screen-calculator-r18-audit-v1','attempt_id':conditions['attempt_id'],'frozen_manifest_matches':manifest_ok,'baseline':uia['display_digits'],'observation':{'status':report['status'],'frame':report['observation']['frame'],'region':report['observation']['region'],'dimensions':[img.width,img.height],'png_sha256':sha(run/'observation-image-00.png'),'all_black':img.getbbox() is None,'target_generation':report['target_generation'],'input_dispatched':report['input_dispatched']},'dispatch_files_present':any('dispatch' in x.name for x in run.iterdir()),'close':{'status':close['status'],'call_count':close['session']['call_count'],'unresolved_call_ids':close['session']['unresolved_call_ids']},'runner_stop':error,'disposition':'PRE_INPUT_STOP: the frozen runner prompt named 1,043 while the preregistered baseline was 1,044; the observation showed 1,044 and no input was sent.'}
assert manifest_ok and report['status']=='returned' and report['input_dispatched'] is False
assert uia['display_digits']=='1044' and img.getbbox() is not None
assert close['status']=='closed' and close['session']['call_count']==0 and not audit['dispatch_files_present']
(run/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(audit,ensure_ascii=True,indent=2))
