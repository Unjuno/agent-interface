import json,hashlib,sys
from pathlib import Path
from PIL import Image,ImageOps
b=Path(sys.argv[1]);summary={}
for n in ('a01','a02'):
 p=b/('wslc-calc-delayed-target-effect-20261031-'+n);o=p/'output';read=lambda name:json.loads((o/name).read_text());assert (p/'container.exit').read_text().strip()=='0';r=read('result.json');pair=read('pair-synced.json');owner=read('owner-outcome.json');ready=read('ready.json');assert owner['status']=='unknown' and owner['reason']=='transaction_deadline' and owner['worker_retired'] and r['target'] in pair['chain'] and r['calc_pid']==ready['calc_pid'] and r['target']==ready['target'];assert r['start_ns']<pair['sent_ns']<r['deadline_ns']<=r['owner_returned_ns']<r['mid_observed_ns']<r['after_observed_ns']<r['final_observed_ns'] and r['final_observed_ns']>r['scheduled_late_ns'] and not r['late_artifact_present'] and r['buttons_after']==0 and not (o/'fallback-release.txt').exists();assert hashlib.sha256((p/'blank.fods').read_bytes()).hexdigest()==r['document_sha256']
 hashes=[]
 for label,seq in [('before',r['before_sequence']),('mid',r['mid_sequence']),('after',r['after_sequence'])]:
  f=next((o/'owner').rglob(f'observation-{seq}.json'));ob=json.loads(f.read_text());a=ob['native']['artifact'];path=o/a['path'].removeprefix('/out/');blob=path.read_bytes();assert hashlib.sha256(blob).hexdigest()==a['sha256'];im=Image.open(path).convert('RGB');crop=im.crop((0,97,42,119));digest=hashlib.sha256(crop.tobytes()).hexdigest();assert digest==r['ocr'][label]['sha256'];expected=ImageOps.expand(crop.resize((168,88)).crop((25,4,118,82)),border=12,fill='white');assert expected.tobytes()==Image.open(o/(label+'-ocr-crop.png')).convert('RGB').tobytes();hashes.append(digest)
 assert hashes[0]=='2e86f3a0f6d87ee4fb4e5ffeb7cfd159d715cb5f6f8177b0ede83784d49088cf' and r['ocr']['after']['text']=='A2' and r['ocr']['after']['exit']==0
 if n=='a01':assert hashes[1]==hashes[2]!=hashes[0]
 else:
  stop=read('target-stopped.json');resume=read('target-resumed.json');assert stop['state']=='T' and stop['pid']==resume['pid']==r['calc_pid'] and stop['stopped_ns']<pair['sent_ns'] and r['mid_observed_ns']<resume['resumed_ns']<r['after_observed_ns'];assert hashes[1]==hashes[0]!=hashes[2] and r['ocr']['mid']['text']!='A2'
 summary[n]={'owner_status':owner['status'],'namebox_before_equals_mid':hashes[0]==hashes[1],'namebox_mid_equals_after':hashes[1]==hashes[2],'ocr_after':r['ocr']['after']['text'],'buttons_after':r['buttons_after'],'late_artifact':r['late_artifact_present']}
print(json.dumps(summary,indent=2))
