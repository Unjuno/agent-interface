"""Independent offline audit for construction01 raw MCP receipts."""
import hashlib, json, sys
from pathlib import Path

root=Path(sys.argv[1]); out=Path(sys.argv[2]); errors=[]
def read(p):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception as e: errors.append(f'{p.name}: unreadable {type(e).__name__}'); return {}
def response(name):
    row=read(root/'mcp'/name); blocks=row.get('content',[])
    texts=[x.get('text','') for x in blocks if x.get('type')=='text']
    if len(texts)!=1: errors.append(f'{name}: expected one text block'); return {}
    try: return json.loads(texts[0])
    except Exception: errors.append(f'{name}: invalid MCP JSON'); return {}
result=read(root/'result.json'); trace=result.get('construction_trace',{})
expected_session=trace.get('close',{}).get('session_id')
ids={}
for name in ('01-initial-observe','02-inspect-focused','03-review-target','04-stale-binding-dispatch','05-fresh-neutral-dispatch','06-close'):
    p=response(name+'.json'); ids[name]=p.get('call_id')
    if not ids[name]: errors.append(f'{name}: missing call id')
    if p.get('session',{}).get('session_id') != expected_session:
        errors.append(f'{name}: session lineage mismatch')
ins=response('02-inspect-focused.json'); rev=response('03-review-target.json')
stale=response('04-stale-binding-dispatch.json'); fresh=response('05-fresh-neutral-dispatch.json'); close=response('06-close.json')
rawst=stale.get('receipt',{}).get('source',{}).get('raw_report',{}).get('result',{})
rawfr=fresh.get('receipt',{}).get('source',{}).get('raw_report',{}).get('result',{})
seq=[]
for n,cid in ids.items():
    folders=list((root/'server-receipts').glob(cid))
    if len(folders)!=1: errors.append(f'{n}: no unique retained receipt directory'); continue
    req=read(folders[0]/'request.json'); report=read(folders[0]/'report.json')
    if req.get('operation') not in ('observe','inspect_target','review_target','dispatch','close'): errors.append(f'{n}: unexpected operation')
    if report.get('schema') not in ('agent-interface/runtime-observation-v1','agent-interface/runtime-dispatch-result-v1',None):
        errors.append(f'{n}: unexpected report schema')
    seq.append(req.get('operation'))
if seq != ['observe','inspect_target','review_target','dispatch','dispatch','close']:
    errors.append('server request order mismatch: '+repr(seq))
evidence=ins.get('evidence',{}); oldrev=read(root/'result.json').get('construction_trace',{}).get('old_binding_revision')
newrev=rev.get('binding_revision')
if ins.get('status')!='needs_review' or evidence.get('title')!='Open' or evidence.get('window_id')==evidence.get('family_root'):
    errors.append('focused Calc Open modal identity not established')
if rev.get('status')!='target_reviewed' or newrev != oldrev+1 or rev.get('window_id')!=evidence.get('window_id'):
    errors.append('review/revision transition invalid')
if rawst.get('error')!='STALE_BINDING' or rawst.get('backend_emissions')!=0:
    errors.append('old-binding refusal was not zero-emission STALE_BINDING')
release=(rawfr.get('execution',{}).get('releases') or [{}])[0]
if rawfr.get('status')!='completed' or release.get('verified') is not True or release.get('keys_down')!=[] or release.get('buttons_down')!=[]:
    errors.append('fresh revision action or neutral release gate failed')
if close.get('status')!='closed' or close.get('release_attempted') is not True:
    errors.append('close/release report inconsistent')
if result.get('decision')!='PASS_CONSTRUCTION_BINDING_REVIEW_SCOPED': errors.append('runner decision not scoped pass')
hashes={}
for p in sorted(root.rglob('*')):
    if p.is_file() and p != out:
        hashes[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest()
audit={'decision':'PASS_RAW_AUDIT' if not errors else 'FAIL_RAW_AUDIT','errors':errors,'request_order':seq,'stale_error':rawst.get('error'),'stale_backend_emissions':rawst.get('backend_emissions'),'fresh_status':rawfr.get('status'),'release_verified':release.get('verified'),'file_sha256':hashes}
out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(audit,sort_keys=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in audit.items() if k!='file_sha256'},sort_keys=True)); raise SystemExit(0 if not errors else 2)

