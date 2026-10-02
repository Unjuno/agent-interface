import base64,copy,hashlib,json,subprocess
from pathlib import Path
from openpyxl import load_workbook
root=Path(__file__).resolve().parent;case=root/'case'
def require(value,reason):
 if not value:raise ValueError(reason)
def read(path):return json.loads(path.read_text())
def audit(d):
 rows=d['rows'];req=d['requests'];meta=d['metadata']
 require([r['status'] for r in rows]==['ready']+['returned']*13+['terminal'],'ordered stream')
 require([r['result']['id'] for r in rows[1:-1]]==list(range(1,14)),'ordered explicit IDs')
 require(all(r['result']['caller_state']['stopped'] is None for r in rows[1:-1]),'no hidden STOP')
 require(req[7]['args'][0]=='interface_inspect_target' and req[9]['args'][0]=='interface_review_target','explicit public modal tools')
 require(req[9]['args'][1]==meta[7]['review_request']['arguments'],'original one-use selection')
 require(meta[7]['authority_granted'] is False and meta[7]['input_dispatched'] is False,'inspection not authority')
 require(meta[9]['status']=='target_reviewed' and meta[9]['capture_consistency']=='matched' and meta[9]['binding_revision']==2,'actual selection transition')
 require(req[11]['args'][1]['current_binding_revision']==2,'updated input binding')
 for i in (5,11):
  m=meta[i];require(m['outcome_summary']['execution_status']=='completed','completed input')
  releases=m['receipt']['execution_summary']['releases']
  require(bool(releases) and all(r['verified'] is True and r['keys_down']==[] and r['buttons_down']==[] for r in releases),'neutral input release')
 require(meta[13]['status']=='closed' and meta[13]['release']['verified'] is True and meta[13]['release']['keys_down']==[] and meta[13]['release']['buttons_down']==[],'neutral public close')
 require(rows[-1]['exit']=={'code':0,'signal':None} and d['cleanup']['host_exit']==0,'terminal owner transport')
 require(d['cells']=={'A1':317,'A2':529} and d['score']['actual_nonempty_cells']==d['cells'] and d['score']['success'] is True,'independent persisted cells')
 for i,attempt in [(1,1),(5,3),(7,4),(9,5),(11,6)]:
  result=rows[i]['result'];require(len(result['images'])==1,'one original PNG per presentation')
  desc=result['images'][0];raw=Path(desc['path']).read_bytes()
  block=next(b for b in d['replies'][i]['result']['content'] if b['type']=='image')
  require(raw==base64.b64decode(block['data']) and hashlib.sha256(raw).hexdigest()==desc['sha256'],'image byte identity')
  review=d['reviews'][attempt]
  require(review['relay_id']==attempt and review['images'][0]['sha256']==desc['sha256'],'explicit original image review')
  require(review['reply_sha256']==hashlib.sha256((case/'host'/f'reply-{attempt}.json').read_bytes()).hexdigest(),'review reply identity')
 events=d['events'];first=events[0]['host_monotonic_ms'];last=events[-1]['host_monotonic_ms']
 return {'host_first_send_to_close_ms':last-first,'public_requests':7,'primary_commands':13,'delivered_images':5,'input_programs':2,'task_success':True}
rows=[json.loads(l) for l in (case/'primary-stream.jsonl').read_text().splitlines()]
requests={i:read(case/'exchange'/f'request-{i}.json') for i in range(1,14)}
replies={i:read(case/'exchange'/f'original-reply-{i}.json') for i in [1,3,5,7,9,11,13]}
metadata={i:json.loads(next(b['text'] for b in reply['result']['content'] if b['type']=='text')) for i,reply in replies.items()}
for i in range(1,14):require(rows[i]['result']==read(case/'exchange'/f'presentation-{i}.json'),'exact retained stream presentation')
book=load_workbook(case/'sheet-1001079.xlsx',read_only=True,data_only=True)
cells={c.coordinate:c.value for row in book.active for c in row if c.value is not None};book.close()
d={'rows':rows,'requests':requests,'replies':replies,'metadata':metadata,'reviews':{i:read(case/'host'/f'review-{i}.json') for i in [1,3,4,5,6]},'cells':cells,'score':read(case/'evaluation.json'),'cleanup':read(case/'cleanup.json'),'events':[json.loads(l) for l in (case/'host'/'host-events.jsonl').read_text().splitlines()]}
manifest=read(root/'manifest.json');require(manifest['sha256']==hashlib.sha256((root/'runtime.pyz').read_bytes()).hexdigest(),'archive hash')
for entry in read(root/'host'/'HOST_MANIFEST.json')['files']:
 require(entry['sha256']==hashlib.sha256((root/'host'/entry['path']).read_bytes()).hexdigest(),'host source hash')
metrics=audit(d);negatives=[]
for name in ['wrong-selection-id','old-binding','missing-release','wrong-saved-cell']:
 changed=copy.deepcopy(d)
 if name=='wrong-selection-id':changed['requests'][9]['args'][1]['review_id']='other'
 elif name=='old-binding':changed['requests'][11]['args'][1]['current_binding_revision']=1
 elif name=='missing-release':changed['metadata'][11]['receipt']['execution_summary']['releases']=[]
 else:changed['cells']['A2']=530
 try:audit(changed)
 except ValueError as error:negatives.append({'name':name,'rejected':True,'reason':str(error)})
 else:raise ValueError('negative escaped: '+name)
print(json.dumps({'status':'PASS_PRIMARY_MODAL_PATH_SCOPED','metrics':metrics,'counterexamples':negatives,'scope':'one known-family authored desktop task; not matched efficiency or human tempo'},indent=2))
