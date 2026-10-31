import json,hashlib,sys
from pathlib import Path
from PIL import Image
b=Path(sys.argv[1]);ocrroot=b/'wslc-calc-grab-supervisor-ocr-20261031-a01';ocr=json.loads((ocrroot/'output/result.json').read_text());summary={}
for n in ('a01','a02'):
 p=b/('wslc-calc-grab-supervisor-20261031-'+n);o=p/'output';r=json.loads((o/'result.json').read_text());owner=json.loads((o/'owner-outcome.json').read_text());down=json.loads((o/'down.json').read_text());ready=json.loads((o/'ready.json').read_text());assert ready['owner_pid']!=ready['cleanup_pid'] and owner['worker_retired'] and r['target'] in down['chain'];assert r['buttons_after']==0 and not r['late_artifact_present'];assert not (o/'fallback-release.txt').exists();assert hashlib.sha256((p/'blank.fods').read_bytes()).hexdigest()==r['document_sha256'];imgs=[]
 for seq in (r['before_sequence'],r['after_sequence']):
  f=next((o/'owner').rglob(f'observation-{seq}.json'));ob=json.loads(f.read_text());a=ob['native']['artifact'];image=o/a['path'].removeprefix('/out/');blob=image.read_bytes();assert hashlib.sha256(blob).hexdigest()==a['sha256'];imgs.append(Image.open(image).convert('RGB'))
 hashes=[hashlib.sha256(im.crop((0,97,42,119)).tobytes()).hexdigest() for im in imgs];assert hashes==[r['before_namebox_sha256'],r['after_namebox_sha256']] and hashes[0]!=hashes[1];assert (ocrroot/(n+'.png')).read_bytes()==(o/'namebox-after.png').read_bytes();assert ocr[n]['exit']==0 and ocr[n]['text']=='A2'
 if n=='a01':assert owner['status']=='completed' and owner['worker_exitcode']==0 and r['button_down_before_cleanup'] is False
 else:
  clean=json.loads((o/'cleanup-outcome.json').read_text());assert owner['status']=='unknown' and owner['reason']=='transaction_deadline' and r['button_down_before_cleanup'] is True and clean['cleanup_status']=='UNKNOWN' and clean['release_confirmed'] is False and clean['owner_release_attempt']['status']=='readback_verified' and r['after_observed_ns']>down['scheduled_late_ns']
 summary[n]={'owner_status':owner['status'],'button_down_before_cleanup':r['button_down_before_cleanup'],'buttons_after':r['buttons_after'],'original_ocr':r['ocr_text'],'posthoc_cropped_ocr':ocr[n]['text'],'late_artifact':r['late_artifact_present']}
print(json.dumps(summary,indent=2))
