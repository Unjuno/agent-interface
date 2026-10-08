"""Read-only paired retained projection. No application or model is invoked."""
from pathlib import Path
import json,hashlib,copy
from runtime.cli_v1.review import review, review_bytes
from runtime.cli_v1.receipt_references import expand_receipt
from runtime.cli_v1.public_summary import summarize_retained_dispatch
r=Path(__file__).resolve().parents[3];e=Path(__file__).resolve().parent
prior=r/'runtime/results/inkscape-owned-public-01/fresh-01'
def encode(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
rows=[]
for index in (2,3):
 path=prior/'public'/f'{index:03d}-raw.json';run=prior/'public'
 data=path.read_bytes();full=review_bytes(data,run,compact=True,report_refs=True);before=copy.deepcopy(full)
 summary=summarize_retained_dispatch(full,path,run)
 if full!=before or summary['receipt']['schema']!='agent-interface/receipt-view-dispatch-summary-v1':raise ValueError('projection unavailable or mutated input')
 if summary['image']!=full['image'] or summary['image_reference']!=full['image_reference'] or summary['outcome_summary']!=full['outcome_summary']:raise ValueError('critical feedback differs')
 retrieval=summary['presentation']['retrieve']['arguments']
 recovered=review(retrieval['report'],retrieval['run_directory'],compact=True,report_refs=True,expected_report_sha256=retrieval['expected_report_sha256'],include_image=False)
 if expand_receipt(recovered['receipt'])['report']!=json.loads(data):raise ValueError('full report retrieval differs')
 for name,value in [('full',full),('summary',summary),('retrieved',recovered)]: (e/f'{index:03d}-{name}.json').write_text(json.dumps(value,indent=2)+'\n')
 def text_bytes(view):return len(encode({k:v for k,v in view.items() if k!='image'}))
 rows.append({'command':index,'raw_report_sha256':hashlib.sha256(data).hexdigest(),'image_sha256':full['image_reference']['sha256'],'full_text_bytes':text_bytes(full),'summary_text_bytes':text_bytes(summary),'image_and_outcome_identical':True,'full_retrieval_verified':True,'scope':'same retained image/report, offline text projection; no new model input or GUI action'})
failures=[]
original=json.loads((prior/'public/002-raw.json').read_text())
for name in ('recovery','release_failure','unknown_execution'):
 raw=copy.deepcopy(original)
 if name=='recovery':raw['result']['recovery_required']=True
 elif name=='release_failure':raw['result']['execution']['releases'][0]['verified']=False
 else:raw['result']['execution']['new_evidence']={'unknown':True}
 path=e/(name+'.json');path.write_text(json.dumps(raw))
 full=review_bytes(path.read_bytes(),prior/'public',compact=True,report_refs=True)
 summary=summarize_retained_dispatch(full,path,prior/'public')
 if summary!=full:raise ValueError('unsafe projection '+name)
 failures.append({'case':name,'full_view_preserved':True,'synthetic_retained_variant':True,'input_dispatched':False})
(e/'pairs.json').write_text(json.dumps({'pairs':rows,'failure_variants':failures,'model_tokens':None,'billing':None,'scope':'byte comparison only; semantic task evidence remains frozen prior source'},indent=2)+'\n')
print(json.dumps(rows));print(failures)
