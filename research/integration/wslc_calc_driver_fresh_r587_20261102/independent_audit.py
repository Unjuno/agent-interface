import hashlib,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
root=Path(sys.argv[1]);out=root/'output';run=json.loads((root/'integration-result.json').read_text());producer=json.loads((out/'result.json').read_text())
T='{urn:oasis:names:tc:opendocument:xmlns:table:1.0}';O='{urn:oasis:names:tc:opendocument:xmlns:office:1.0}'
xml=ET.parse(out/'saved.fods').getroot();sheets=xml.findall('.//'+T+'table');cells=[]
if len(sheets)!=1:raise ValueError('unexpected sheet count')
rows=sheets[0].findall(T+'table-row')
if len(rows)!=len(sheets[0].findall('.//'+T+'table-row')):raise ValueError('nested rows unsupported')
r=0
for row in rows:
 repeat=int(row.get(T+'number-rows-repeated','1'));c=0
 if repeat<1:raise ValueError('invalid row repeat')
 for cell in row:
  if cell.tag not in (T+'table-cell',T+'covered-table-cell'):continue
  count=int(cell.get(T+'number-columns-repeated','1'));value=cell.get(O+'value');formula=cell.get(T+'formula');kind=cell.get(O+'value-type');text=''.join(cell.itertext()).strip()
  if count<1:raise ValueError('invalid column repeat')
  if any(x is not None for x in (value,formula,kind)) or text:
   if repeat!=1 or count!=1:raise ValueError('repeated nonempty cell')
   cells.append([r,c,kind,value,text,formula])
  c+=count
 r+=repeat
expected=[[0,0,'float','472','472',None],[1,0,'float','615','615',None]]
def neutral(v):return isinstance(v,dict) and v.get('verified') is True and v.get('keys_down')==[] and v.get('buttons_down')==[]
actions={}
for name in ('click-result.json','fresh-entry.json','fresh-save.json'):
 a=json.loads((out/name).read_text());rs=a.get('execution',{}).get('releases');actions[name]=a.get('status')=='completed' and isinstance(rs,list) and len(rs)>0 and all(neutral(x) for x in rs)
gate=json.loads((out/'stale-gate.json').read_text());responses=[]
for i in (1,2,3):
 q=json.loads((root/'exchange'/f'request-{i}.json').read_text());answer=json.loads((root/'exchange'/f'response-{i}.json').read_text());digest=hashlib.sha256((root/'exchange'/f'image-{i}.png').read_bytes()).hexdigest()
 responses.append({'request_id':q.get('id'),'sequence':q.get('source_sequence'),'digest_matches':q.get('image_sha256')==digest==answer.get('image_sha256'),'fixture_flag':answer.get('fixture') is True})
receipt=run.get('reconcile',{}).get('remove',{});close=producer.get('close',{})
audit={'fods_sha256':hashlib.sha256((out/'saved.fods').read_bytes()).hexdigest(),'independent_xml_values':cells,'expected_values':expected,'effect_pass':cells==expected,'actions_released':actions,'owner_close_verified':close.get('status')=='closed' and neutral(close.get('release')),'final_neutral':producer.get('keys_down')==[] and type(producer.get('buttons')) is int and producer['buttons']==0,'stale_difference_detected_before_mint':gate.get('binding_unchanged') is True and gate.get('prior_programs_or_mints')==[] and bool(gate.get('before_sha256')) and bool(gate.get('after_sha256')) and gate.get('before_sha256')!=gate.get('after_sha256'),'fixture_requests':responses,'fixture_sequence_increased':all(type(x['sequence']) is int for x in responses) and all(responses[i+1]['sequence']>responses[i]['sequence'] for i in range(len(responses)-1)),'exit_code':run.get('wait',{}).get('exit_code'),'cleanup_status':receipt.get('status'),'elapsed_seconds':(run['ended_ns']-run['started_ns'])/1e9,'not_a_model_or_benchmark':True}
(root/'independent-audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8');print(json.dumps({'effect':audit['effect_pass'],'actions':audit['actions_released'],'neutral':audit['final_neutral'],'close':audit['owner_close_verified'],'stale':audit['stale_difference_detected_before_mint'],'requests':len(responses),'exit':audit['exit_code'],'cleanup':audit['cleanup_status']}))
