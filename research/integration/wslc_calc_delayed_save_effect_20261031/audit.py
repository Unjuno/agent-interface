import json,hashlib,sys,xml.etree.ElementTree as ET
from pathlib import Path
b=Path(sys.argv[1]);summary={};T='{urn:oasis:names:tc:opendocument:xmlns:table:1.0}';O='{urn:oasis:names:tc:opendocument:xmlns:office:1.0}'
def values(blob):
 root=ET.fromstring(blob);sheets=root.findall('.//'+T+'table');assert len(sheets)==1;sheet=sheets[0];rows=sheet.findall(T+'table-row');assert len(rows)==len(sheet.findall('.//'+T+'table-row'));result=[]
 for ri,row in enumerate(rows):
  col=0
  for cell in row:
   if cell.tag not in (T+'table-cell',T+'covered-table-cell'):continue
   count=int(cell.get(T+'number-columns-repeated','1'));assert cell.get(T+'formula') is None;kind=cell.get(O+'value-type');val=cell.get(O+'value');text=''.join(cell.itertext()).strip()
   if kind is not None or val is not None or text:assert count==1 and int(row.get(T+'number-rows-repeated','1'))==1;result.append((ri,col,kind,val,text))
   col+=count
 return result
for n in ('a01','a02'):
 p=b/('wslc-calc-delayed-save-effect-20261031-'+n);o=p/'output';read=lambda name:json.loads((o/name).read_text());assert (p/'container.exit').read_text().strip()=='0';r=read('result.json');pair=read('save-synced.json');owner=read('owner-outcome.json');entry=read('entry-result.json');cue=read('filled-cue.json');ready=read('ready.json');assert owner['status']=='unknown' and owner['reason']=='transaction_deadline' and owner['worker_retired'];assert r['target'] in pair['focus_chain'] and r['target']==ready['target'] and r['calc_pid']==ready['calc_pid'];assert entry['status']=='completed' and entry['execution']['releases'] and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in entry['execution']['releases']) and cue['cue']=='filled';assert r['start_ns']<pair['sent_ns']<r['deadline_ns']<=r['owner_returned_ns']<r['mid_observed_ns']<=r['after_observed_ns']<r['final_observed_ns'] and r['final_observed_ns']>r['scheduled_late_ns'] and not r['late_artifact_present'] and r['keys_down']==[] and r['buttons_after']==0 and not (o/'fallback-keys.txt').exists();mid=(o/'mid.fods').read_bytes();after=(o/'after.fods').read_bytes();assert hashlib.sha256(mid).hexdigest()==r['mid_sha256'] and hashlib.sha256(after).hexdigest()==r['after_sha256'] and hashlib.sha256((p/'blank.fods').read_bytes()).hexdigest()==r['baseline_sha256'];assert values(after)==[(0,0,'float','731','731'),(1,0,'float','864','864')]
 if n=='a01':assert values(mid)==values(after) and r['mid_sha256']!=r['baseline_sha256']
 else:
  stop=read('target-stopped.json');resume=read('target-resumed.json');assert stop['state']=='T' and stop['pid']==resume['pid']==r['calc_pid'] and stop['stopped_ns']<pair['sent_ns'] and r['mid_observed_ns']<resume['resumed_ns']<r['after_observed_ns'];assert r['mid_sha256']==r['baseline_sha256'] and values(mid)==[] and r['after_sha256']!=r['baseline_sha256']
 summary[n]={'owner_status':owner['status'],'saved_at_owner_return':r['mid_sha256']!=r['baseline_sha256'],'saved_after_resume':values(after)==[(0,0,'float','731','731'),(1,0,'float','864','864')],'keys_down':r['keys_down'],'buttons':r['buttons_after'],'late_artifact':r['late_artifact_present']}
print(json.dumps(summary,indent=2))
