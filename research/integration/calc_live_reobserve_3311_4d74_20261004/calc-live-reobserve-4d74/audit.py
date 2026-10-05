import json,pathlib,hashlib,base64
from PIL import Image
from saved_oracle import score_saved
R=pathlib.Path('/data');D=R/'runs/live_reobserve18';O=pathlib.Path('/out');raw=json.loads((D/'raw.json').read_text());plan=json.loads((R/'PLAN.json').read_text());record=json.loads((D/'model-batch/HOST_RECORD.private.json').read_text());errors=[]
for n,h in plan['source_hashes'].items():
 if hashlib.sha256((R/n).read_bytes()).hexdigest()!=h:errors.append('source '+n)
effect=score_saved((D/'first.fods').read_bytes(),13,41)
if not effect['pass_effect']:errors.append('first effect')
captures=raw['images']+[x['prior'] for x in raw.get('read_continuations',[])]+[raw['final_guarded']]
for im in captures:
 a=im['native']['artifact'];p=D/'guarded/images'/pathlib.PurePosixPath(a['path']).name
 if hashlib.sha256(p.read_bytes()).hexdigest()!=a['sha256']:errors.append('capture')
for im,check in zip(raw['images'],raw['pixel_checks']):
 p=D/'guarded/images'/pathlib.PurePosixPath(im['native']['artifact']['path']).name
 if hashlib.sha256(Image.open(p).convert('RGB').crop((36,161,305,175)).tobytes()).hexdigest()!=check['rgb_sha256']:errors.append('ROI association')
requests=[x for x in record['received'] if x.get('method')=='item/tool/call'];reply=next(x['result'] for x in record['sent'] if x.get('id')==requests[0]['id'] and 'result' in x);image=next(x['imageUrl'] for x in reply['contentItems'] if x['type']=='inputImage');digest=hashlib.sha256(base64.b64decode(image.split(',',1)[1])).hexdigest();expected=raw['final_guarded']['native']['artifact']['sha256']
turns=[x for x in record['sent'] if x.get('method')=='turn/start'];local=next(x for x in turns[1]['params']['input'] if x['type']=='localImage');p=D/'guarded/images'/pathlib.PureWindowsPath(local['path']).name
if digest!=expected or hashlib.sha256(p.read_bytes()).hexdigest()!=expected:errors.append('model image delivery')
if len(requests)!=1 or len(turns)!=2 or len(raw['native_attempts'])!=1 or (D/'second.fods').exists():errors.append('attempt counts')
if raw['cleanup_physical']['keys'] or raw['cleanup_physical']['buttons'] or not raw['cleanup_release']['verified']:errors.append('release')
ocr=[json.loads(s) for s in (D/'OCR_ATTEMPTS.jsonl').read_text().splitlines()]
messages=[x['params']['item'].get('text','') for x in record['received'] if x.get('method')=='item/completed' and x.get('params',{}).get('item',{}).get('type')=='agentMessage']
out=dict(scope='G18_CURRENT_MAIN_LIVE_PARTIAL_AND_REOBSERVATION_CUSTODY',errors=errors,saved_effect=effect,messages=messages,graph=raw['compiled_result']['outcome'],reason=raw['compiled_result']['reason'],native_programs=len(raw['native_attempts']),continuations=len(raw.get('read_continuations',[])),ocr_attempts=len(ocr),ocr_total_ns=sum(x['end_ns']-x['start_ns'] for x in ocr),model_usage=record['usage'],cgroups=raw['cgroups'],source_main=plan['source_main'],feedback_sha256=expected,limitation='Primary semantic scoring separate; no broad accuracy or efficiency inference.')
with (O/'AUDIT.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out));raise SystemExit(bool(errors))
