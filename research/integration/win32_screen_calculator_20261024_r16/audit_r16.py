from pathlib import Path
import hashlib,json
from PIL import Image
p=Path(__file__).resolve().parent;run=p/'run'
def j(n):return json.loads((run/n).read_text(encoding='utf-8'))
def sha(x):return hashlib.sha256(x.read_bytes()).hexdigest()
conditions=json.loads((p/'conditions.json').read_text(encoding='utf-8'))
obs=j('observation-parsed.json'); report=obs['receipt']['report']; image=Image.open(run/'observation-image-00.png').convert('RGB')
close=j('close.json');uia=j('uia-preflight.json')['parsed']
frozen={}
for line in (p/'FROZEN_SHA256SUMS').read_text(encoding='ascii').splitlines():h,n=line.split('  ',1);frozen[n]=h
manifest_ok=all(sha(p/n)==h for n,h in frozen.items())
result={'schema':'win32-screen-calculator-r16-audit-v1','attempt_id':conditions['attempt_id'],'frozen_manifest_matches':manifest_ok,'observation_status':report['status'],'frame':report['observation']['frame'],'region':report['observation']['region'],'dimensions':[image.width,image.height],'png_sha256':sha(run/'observation-image-00.png'),'all_black':image.getbbox() is None,'uia_display':uia['display_digits'],'visible_value_in_image':'1043 (visually inspected)','target_generation':report['target_generation'],'input_dispatched':report['input_dispatched'],'session_call_count_at_observation':report['session']['call_count'],'close_status':close['status'],'close_call_count':close['session']['call_count'],'unresolved_call_ids':close['session']['unresolved_call_ids'],'disposition':'READ_ONLY_CAPTURE_PASS: screen_physical_px produced a non-black Calculator view showing 1,043; no input was issued','limits':'No dispatch, release test, task oracle, recovery, efficiency or reliability evidence.'}
assert manifest_ok and report['status']=='returned' and report['input_dispatched'] is False
assert report['session']['call_count']==0 and close['session']['call_count']==0 and close['status']=='closed'
assert image.size==(320,533) and image.getbbox() is not None and uia['display_digits']=='1043'
(run/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=True,indent=2))
