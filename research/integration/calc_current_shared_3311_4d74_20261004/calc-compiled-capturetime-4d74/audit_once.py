import hashlib,json,pathlib
from saved_oracle import score_saved
root=pathlib.Path(__file__).resolve().parent;run=root/'runs/compiled_capturetime05'
raw=json.loads((run/'raw.json').read_text(encoding='utf-8'));host=json.loads((run/'HOST_RECEIPT.json').read_text(encoding='utf-8'))
effect=score_saved((run/'saved.fods').read_bytes(),31,37)
graph=raw['compiled_result'];attempts=raw['native_attempts'];errors=[]
def require(value,reason):
    if not value:errors.append(reason)
require(not raw['errors'] and host['exit_code']==0,'native or host failure')
require(graph['outcome']=='SAFE_YIELD' and graph['reason']=='effect_unavailable','unknown effect did not yield')
require(graph['completed_transitions']==1 and len(graph['transitions'])==1,'wrong transition inventory')
require(len(attempts)==1 and len(raw['graph_admissions'])==1,'second input/admission occurred')
require(len(graph['observations'])==2,'fresh post-input observation missing')
require(all(x['predicates']['saved_effect']=='unknown' for x in graph['observations']),'unknown effect was relabeled')
require(len(raw.get('verifier_calls',[]))==0,'unknown predicate reached success verifier')
require(effect['pass_effect'],'saved XML effect/collateral failed')
receipt=attempts[0]
require(receipt['status']=='completed','first native input did not complete')
require([x['stage'] for x in receipt['guard_checks']]==['before_admission','before_focus','before_move','before_press'],'native guard stages')
require(all(x['status']=='VALID' and x['eligible'] for x in receipt['guard_checks']),'guard refusal')
releases=receipt['execution']['releases']
require(bool(releases) and all(x['verified'] is True and x['keys_down']==[] and x['buttons_down']==[] for x in releases),'public release')
for key in ('post_dispatch_physical','cleanup_physical'):
    require(raw[key]['keys']==[] and raw[key]['buttons']==0,key)
require(len(raw['terminal'])==3 and all(x['exit_code'] in (0,255) for x in raw['terminal']),'tracked parent terminal')
for observation in [raw['initial_guarded'],*raw['images'],raw['final_guarded']]:
    art=observation['native']['artifact'];p=run/'guarded/images'/art['path'].rsplit('/',1)[-1]
    require(hashlib.sha256(p.read_bytes()).hexdigest()==art['sha256'],'PNG digest')
for graph_observation,native_observation in zip(graph['observations'],raw['images']):
    require(graph_observation['captured_ns']==native_observation['native']['capture_started_ns'],'capture time binding')
out=dict(disposition='PASS_SCOPED_UNKNOWN_EFFECT_YIELD' if not errors else 'FAIL',errors=errors,graph_outcome=graph['outcome'],graph_reason=graph['reason'],native_attempts=len(attempts),admissions=len(raw['graph_admissions']),completed_transitions=len(graph['transitions']),observations=len(graph['observations']),saved_effect=effect,cgroups=raw['cgroups'],primary_usage='UNKNOWN',additional_benchmark_client_calls=0,limits='intentional semantic-predicate unavailability; no semantic detector efficacy, broad release, same-model comparison or token benefit')
target=root/'AUDIT.json'
if target.exists():raise RuntimeError('first auditor output retained; replay refused')
target.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in out.items() if k!='saved_effect'}));raise SystemExit(bool(errors))
