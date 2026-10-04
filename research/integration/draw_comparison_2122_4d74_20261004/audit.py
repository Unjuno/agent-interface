import pathlib,json,hashlib,xml.etree.ElementTree as ET
R=pathlib.Path('/study');O=pathlib.Path('/out');raw=json.loads((O/'RAW.json').read_text());models=json.loads((O/'MODEL.json').read_text());errors=[];scores=[];cost={'input_tokens':0,'output_tokens':0,'cached_input_tokens':0,'reasoning_output_tokens':0};calls={c['id']:c for c in models['calls']}
ns={'draw':'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0','svg':'urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0'}
def units(v):
 if v.endswith('cm'):return round(float(v[:-2])*1000)
 if v.endswith('mm'):return round(float(v[:-2])*100)
 raise ValueError(v)
for row in raw['rows']:
 name=row['id'];p=O/(name+'.fodg')
 if not p.exists():errors.append('missing_saved:'+name);continue
 if hashlib.sha256(p.read_bytes()).hexdigest()!=row['saved_sha256']:errors.append('hash:'+name)
 rects=ET.parse(p).findall('.//draw:rect',ns);saved={s.get('{'+ns['draw']+'}name'):[units(s.get('{'+ns['svg']+'}'+k)) for k in ['x','y','width','height']] for s in rects}
 mutated=row['case'] in ['conflict_locked','unknown_locked','blind_stale_negative'];expected={'A':[1900 if mutated else 1200,1000,500,500],'B':[2700 if mutated else 2000,1000,500,500]};task=saved==expected
 if mutated:
  if row.get('writer_exit')!=0 or row['writer']['pid']==raw['controller_pid'] or row['writer']['after']!=[['A',1700,1000],['B',2700,1000]]:errors.append('writer:'+name)
 observed={v['name']:v['position']+v['size'] for v in row['observer']['objects']} if row.get('observer') else None
 if observed!=saved or row.get('observer_exit')!=0:errors.append('observer:'+name)
 if row['arm']!='negative' and (row['membership_matches']!=1 or not row['bound_guard']):errors.append('binding:'+name)
 if row['arm']=='negative':
  if task or saved.get('A',[None])[0]!=1200:errors.append('negative_not_exposed')
 else:
  if not task:errors.append('task:'+name)
  if row['input_mutations']!=1:errors.append('mutation_count:'+name)
 if row['arm']=='model':
  c=calls.get(name)
  if not c or not c['transport_ok'] or c['answer']!=row['response']['answer']:errors.append('model_join:'+name)
  else:
   for k in cost:cost[k]+=c['completed'][0]['usage'].get(k,0)
 scores.append({'id':name,'saved':saved,'expected':expected,'task_complete':task,'action':row['action'],'disposition':row['disposition']})
if len(raw['rows'])!=9 or len(calls)!=4 or raw['errors'] or raw['parent_exit']!=0:errors.append('coverage_or_exit')
print(json.dumps({'scores':scores,'cost':cost,'model_host_elapsed_ns':sum(c['elapsed_ns'] for c in calls.values()),'errors':errors,'decision':'SUPPORT_FRESH_READ_RECOVERY_SCOPED' if not errors else 'FAIL_OR_HOLD','scope':'actual fixed-order headless Draw/model/API recovery; finite barriers only, no atomic current authority or model advantage'},indent=2));raise SystemExit(bool(errors))
