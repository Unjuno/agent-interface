import json,pathlib,hashlib
from saved_oracle import score_saved
R=pathlib.Path(__file__).resolve().parent;D=R/'runs/measured_shared11';raw=json.loads((D/'raw.json').read_text());errors=[]
def check(v,s):
    if not v:errors.append(s)
effects=[score_saved((D/(n+'.fods')).read_bytes(),a,b) for n,a,b in [('first',17,23),('second',37,43)]]
check(all(e['pass_effect'] for e in effects),'independent saved effects')
g=raw['compiled_result'];check(g['outcome']=='TASK_SUCCEEDED' and len(g['transitions'])==2,'graph completion')
check(len(raw['native_attempts'])==2 and len(raw['graph_admissions'])==2 and len(g['observations'])==3,'inventory')
ocr=[json.loads(v) for v in (D/'OCR_ATTEMPTS.jsonl').read_text().splitlines()]
check([v['stdout'].strip() for v in ocr]==['','17','23','391','37','43','1591'],'all-attempt OCR transcript')
check(all(v['exit_code']==0 for v in ocr),'OCR exits')
for receipt in raw['native_attempts']:
    check(receipt['status']=='completed','native terminal');check([v['stage'] for v in receipt['guard_checks']]==['before_admission','before_focus','before_move','before_press'],'four guards')
    check(all(v['status']=='VALID' and v['eligible'] for v in receipt['guard_checks']),'valid guards')
    check(all(v['verified'] is True and v['keys_down']==[] and v['buttons_down']==[] for v in receipt['execution']['releases']),'release')
for v in [*raw['physical_checks'],raw['cleanup_physical']]:check(v['keys']==[] and v['buttons']==0,'physical release')
for graph,image in zip(g['observations'],raw['images']):
    a=image['native']['artifact'];p=D/'guarded/images'/a['path'].rsplit('/',1)[-1];check(hashlib.sha256(p.read_bytes()).hexdigest()==a['sha256'],'PNG digest');check(graph['captured_ns']==image['native']['capture_started_ns'],'native time')
client=json.loads((R/'CLIENT_RECEIPT.json').read_text());model=json.loads((D/'model-batch/HOST_RECORD.private.json').read_text());check(client['native_exit']==0 and client['model_summary']['dynamic_calls']==1 and not model['errors'],'actual model client')
check(model['model_input_png_sha256']==raw['initial_guarded']['native']['artifact']['sha256'] and model['model_feedback_png_sha256']==raw['final_guarded']['native']['artifact']['sha256'],'actual offered image binding')
out={'disposition':'PASS_SCOPED_MEASURED_SHARED_CLIENT' if not errors else 'FAIL','errors':errors,'saved_effects':effects,'ocr_calls':len(ocr),'ocr_local_elapsed_ns':sum(v['end_ns']-v['start_ns'] for v in ocr),'primary_usage':'UNKNOWN','native_programs':len(raw['native_attempts'])}
p=R/'AUDIT.json'
if p.exists():raise RuntimeError('first auditor output exists')
p.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='saved_effects'}));raise SystemExit(bool(errors))
