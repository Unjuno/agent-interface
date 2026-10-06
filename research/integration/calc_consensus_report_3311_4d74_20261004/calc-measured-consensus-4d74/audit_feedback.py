"""Independent saved transcript/capture audit; never calls model or GUI."""
import base64,hashlib,json,pathlib
R=pathlib.Path(__file__).resolve().parent;D=R/'runs/measured_consensus14'
raw=json.loads((D/'raw.json').read_text(encoding='utf-8'));record=json.loads((D/'model-batch/HOST_RECORD.private.json').read_text(encoding='utf-8'));done=json.loads((D/'batch.DONE.json').read_text(encoding='utf-8'));errors=[]
captures=raw['images']+[x['prior'] for x in raw.get('read_continuations',[])]+[raw['final_guarded']]
for im in captures:
 a=im['native']['artifact'];p=D/'guarded/images'/pathlib.Path(a['path']).name
 if hashlib.sha256(p.read_bytes()).hexdigest()!=a['sha256']:errors.append('capture hash')
 if im['native']['capture_started_ns']>im['native']['capture_ended_ns']:errors.append('capture time reversed')
requests=[x for x in record['received'] if x.get('method')=='item/tool/call']
if len(requests)!=1:errors.append('tool request count')
replies=[x for x in record['sent'] if x.get('id')==requests[0]['id'] and 'result' in x]
reply=replies[0]['result'];items=reply['contentItems'];typed=json.loads(next(x['text'] for x in items if x['type']=='inputText'))
image=next(x['imageUrl'] for x in items if x['type']=='inputImage');digest=hashlib.sha256(base64.b64decode(image.split(',',1)[1])).hexdigest()
if digest!=raw['final_guarded']['native']['artifact']['sha256'] or digest!=record['model_feedback_png_sha256']:errors.append('model feedback image')
if reply['success'] is not False or typed['graph_outcome']!='SAFE_YIELD' or typed['reason']!='effect_unavailable' or typed['completed_transitions']!=1:errors.append('typed model partial reply')
consensus=[json.loads(x) for x in (D/'OCR_CONSENSUS.jsonl').read_text(encoding='utf-8').splitlines()]
if len(consensus)!=4 or any(x['agreement'] or x['full']!=['23','41','943'] or x['tight']!=['23','4','943'] for x in consensus):errors.append('consensus raw')
if len(raw['native_attempts'])!=1 or len(raw.get('read_continuations',[]))!=3 or (D/'second.fods').exists():errors.append('no second emission')
messages=[x['params']['item'].get('text','') for x in record['received'] if x.get('method')=='item/completed' and x.get('params',{}).get('item',{}).get('type')=='agentMessage']
out=dict(scope='SAVED_FEEDBACK_AND_INTERMEDIATE_CAPTURE_CUSTODY',errors=errors,capture_records=len(captures),feedback_sha256=digest,typed_reply=typed,model_final_messages=messages,limitation='Image offered/agent final text is not proof of internal attention or comprehension.')
with (R/'FEEDBACK_AUDIT.json').open('x',encoding='utf-8') as f:json.dump(out,f,indent=2)
print(json.dumps(out));raise SystemExit(bool(errors))
