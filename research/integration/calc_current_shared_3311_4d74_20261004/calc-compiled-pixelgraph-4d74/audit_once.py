import hashlib,json,pathlib
from PIL import Image
from saved_oracle import score_saved
root=pathlib.Path(__file__).resolve().parent;folder=root/'runs/compiled_pixelgraph06'
raw=json.loads((folder/'raw.json').read_text(encoding='utf-8'));host=json.loads((folder/'HOST_RECEIPT.json').read_text(encoding='utf-8'));errors=[]
def require(value,reason):
    if not value:errors.append(reason)
graph=raw['compiled_result'];require(not raw['errors'] and host['exit_code']==0,'native error')
require(graph['outcome']=='TASK_SUCCEEDED' and graph['reason']=='method_complete','graph not completed')
require(len(graph['transitions'])==2 and len(raw['native_attempts'])==2 and len(raw['graph_admissions'])==2,'attempt inventory')
require(len(graph['observations'])==3 and len(raw['verifier_calls'])==2,'observations/verifier inventory')
effects=[]
for label,a,b in [('first',31,37),('second',47,53)]:
    scored=score_saved((folder/(label+'.fods')).read_bytes(),a,b);effects.append(scored);require(scored['pass_effect'],label+' saved effect/collateral')
for receipt in raw['native_attempts']:
    require(receipt['status']=='completed','native terminal')
    require([g['stage'] for g in receipt['guard_checks']]==['before_admission','before_focus','before_move','before_press'],'guard stages')
    require(all(g['status']=='VALID' and g['eligible'] for g in receipt['guard_checks']),'guard eligibility')
    releases=receipt['execution']['releases'];require(bool(releases) and all(x['verified'] is True and x['keys_down']==[] and x['buttons_down']==[] for x in releases),'public release')
for state in [*raw['physical_checks'],raw['cleanup_physical']]:require(state['keys']==[] and state['buttons']==0,'physical release')
roi=(36,161,305,175);pixel_rows=[]
for graph_observation,image,check in zip(graph['observations'],raw['images'],raw['pixel_checks']):
    art=image['native']['artifact'];path=folder/'guarded/images'/art['path'].rsplit('/',1)[-1]
    require(hashlib.sha256(path.read_bytes()).hexdigest()==art['sha256'],'PNG digest')
    require(graph_observation['captured_ns']==image['native']['capture_started_ns'],'capture-start binding')
    region=Image.open(path).convert('RGB').crop(roi).tobytes();template=Image.open(root/(check['template']+'_reference.png')).convert('RGB').crop(roi).tobytes();match=region==template
    require(check['matches']==match and graph_observation['predicates']['row_visible']==match,'pixel association')
    pixel_rows.append({'state':check['state'],'matches':match,'rgb_sha256':hashlib.sha256(region).hexdigest()})
require([x['matches'] for x in pixel_rows]==[False,True,True],'pixel progression')
require(len(raw['terminal'])==3 and all(t['exit_code'] in (0,255) for t in raw['terminal']),'tracked parents terminal')
out={'disposition':'PASS_SCOPED_TWO_TRANSITION_PIXEL_GRAPH' if not errors else 'FAIL','errors':errors,'graph_outcome':graph['outcome'],'native_programs':len(raw['native_attempts']),'observations':len(graph['observations']),'pixel_rows':pixel_rows,'saved_effects':effects,'primary_usage':'UNKNOWN','additional_benchmark_client_calls':0,'limits':'Fixed-render known-row image templates, not generic OCR or proof of save persistence from pixels; independent XML scoring separated. No same-model comparison or cost advantage.'}
target=root/'AUDIT.json'
if target.exists():raise RuntimeError('first output exists; no overwrite')
target.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in out.items() if k!='saved_effects'}));raise SystemExit(bool(errors))
