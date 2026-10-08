import hashlib,json,pathlib
from saved_oracle import score_saved
R=pathlib.Path(__file__).resolve().parent;results=[];errors=[]
for ordinal in (1,2,3):
 D=R/'runs'/('guarded0'+str(ordinal));raw=json.loads((D/'raw.json').read_text(encoding='utf-8'));host=json.loads((D/'HOST_RECEIPT.json').read_text(encoding='utf-8'));rows=[]
 if ordinal==1:
  if host['exit_code']!=2 or 'target alias must match' not in ''.join(raw['errors']):errors.append('original alias failure not retained')
  result=dict(ordinal=1,outcome='INVALID_CALLER_ALIAS_PREINPUT',errors=raw['errors'],cleanup=raw.get('cleanup_physical'))
 else:
  if raw['errors'] or host['exit_code']!=0:errors.append('native construction errors '+str(ordinal))
  cases=[('saved.fods',31,37,'guarded_result','after_dispatch_physical','final_guarded')]
  if ordinal==3:cases += [('repair.fods',47,53,'repair_result','repair_physical','repair_image'),('warm.fods',59,61,'warm_result','warm_physical','warm_image')]
  for filename,a,b,key,physical,image_key in cases:
   blob=(D/filename).read_bytes();effect=score_saved(blob,a,b);receipt=raw[key];releases=receipt.get('execution',{}).get('releases',[]);checks=receipt.get('guard_checks',[])
   bad=[]
   if not effect['pass_effect']:bad.append('saved effect/collateral')
   if receipt.get('status')!='completed' or receipt.get('recovery_required') is not False:bad.append('typed native completion')
   if not releases or not all(v.get('verified') is True and v.get('keys_down')==[] and v.get('buttons_down')==[] for v in releases):bad.append('public release')
   if raw[physical]['keys'] or raw[physical]['buttons']:bad.append('physical release')
   if [v['stage'] for v in checks]!=['before_admission','before_focus','before_move','before_press'] or any(v['status']!='VALID' or not v['eligible'] for v in checks):bad.append('four-phase target guards')
   artifact=raw[image_key]['native']['artifact'];path=D/'guarded/images'/artifact['path'].rsplit('/',1)[-1]
   if hashlib.sha256(path.read_bytes()).hexdigest()!=artifact['sha256']:bad.append('original PNG digest')
   rows.append(dict(file=filename,effect=effect,receipt_status=receipt['status'],guard_stages=[v['stage'] for v in checks],saved_sha256=hashlib.sha256(blob).hexdigest(),errors=bad));errors.extend(bad)
  if ordinal==3:
   refusal=raw['reuse_old_result']
   if refusal.get('status')!='refused' or refusal.get('input_dispatched') is not False or raw['reuse_old_emission_delta']!=0 or raw['reuse_old_physical']['keys'] or raw['reuse_old_physical']['buttons']:errors.append('old alias refusal/no emissions')
  if raw['cleanup_physical']['keys'] or raw['cleanup_physical']['buttons']:errors.append('final physical neutral')
  if len(raw['terminal'])!=3 or any(v['exit_code'] not in (0,255) for v in raw['terminal']):errors.append('parent terminal')
  result=dict(ordinal=ordinal,outcome='CONSTRUCTION_SAVED_EFFECT_AND_NATIVE_GUARDS_PASS',rows=rows,old_alias_refusal=raw.get('reuse_old_result'),refusal_emission_delta=raw.get('reuse_old_emission_delta'),cleanup=raw['cleanup_physical'])
 results.append(result)
out=dict(scope='construction only; current primary image grounding with total primary usage UNKNOWN; no additional benchmark model/client calls; no full graph/comparison claim',additional_benchmark_model_calls=0,primary_total_usage='UNKNOWN',errors=errors,results=results)
path=R/'CONSTRUCTION_AUDIT.json'
if path.exists():raise RuntimeError('first reader output exists')
path.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(errors=errors,accepted_programs=4,refused_programs=1,correct_saved_documents=sum(len(v.get('rows',[])) for v in results))));raise SystemExit(bool(errors))
