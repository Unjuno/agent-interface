import hashlib,json,pathlib
from saved_oracle import score_saved
R=pathlib.Path(__file__).resolve().parent;D=R/'runs/compiled_digits08'
raw=json.loads((D/'raw.json').read_text(encoding='utf-8'));host=json.loads((D/'HOST_RECEIPT.json').read_text(encoding='utf-8'));errors=[]
def check(value,label):
    if not value:errors.append(label)
effect=score_saved((D/'first.fods').read_bytes(),23,31);check(effect['pass_effect'],'first saved effect')
graph=raw['compiled_result'];check(graph['outcome']=='SAFE_YIELD' and graph['reason']=='effect_failed','retained native outcome')
check(host['exit_code']==0 and not raw['errors'],'infrastructure')
check(len(raw['native_attempts'])==1 and len(raw['graph_admissions'])==1 and not (D/'second.fods').exists(),'second input unexpectedly occurred')
check(len(raw['pixel_checks'])==2 and raw['pixel_checks'][1]['decoded_values'] is None,'decoder failure missing')
for native in raw['native_attempts']:
    check(native['status']=='completed','native completion')
    check([g['stage'] for g in native['guard_checks']]==['before_admission','before_focus','before_move','before_press'],'four guards')
    check(all(g['status']=='VALID' and g['eligible'] for g in native['guard_checks']),'guard eligibility')
    releases=native['execution']['releases'];check(bool(releases) and all(x['verified'] is True and x['keys_down']==[] and x['buttons_down']==[] for x in releases),'release')
for state in [*raw['physical_checks'],raw['cleanup_physical']]:check(state['keys']==[] and state['buttons']==0,'physical release')
for obs,image in zip(graph['observations'],raw['images']):
    art=image['native']['artifact'];p=D/'guarded/images'/art['path'].rsplit('/',1)[-1]
    check(hashlib.sha256(p.read_bytes()).hexdigest()==art['sha256'],'original image hash')
    check(obs['captured_ns']==image['native']['capture_started_ns'],'capture-time binding')
out={'disposition':'FAIL_HELDOUT_DIGIT_TRANSFER_HOLD_COMPARISON','audit_errors':errors,'first_saved_effect':effect,'native_programs':len(raw['native_attempts']),'graph_reason':graph['reason'],'second_input':0,'scientific_failure':'Actual first saved values correct, glyph reader unavailable; caller collapsed unavailable to false/effect_failed. Positive heldout-transfer gate not met. Second stage censored.','primary_usage':'UNKNOWN'}
p=R/'AUDIT.json'
if p.exists():raise RuntimeError('first audit retained')
p.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in out.items() if k!='first_saved_effect'}));raise SystemExit(bool(errors))
