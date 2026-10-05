import pathlib,json,hashlib,xml.etree.ElementTree as ET
O=pathlib.Path('/out');d=json.loads((O/'RAW.json').read_text());errors=[];scores=[];ns={'draw':'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0','svg':'urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0'}
for r in d['rows']:
 p=O/(r['id']+'.fodg');saved={s.get('{'+ns['draw']+'}name'):[round(float(s.get('{'+ns['svg']+'}'+k)[:-2])*1000) for k in ['x','y','width','height']] for s in ET.parse(p).findall('.//draw:rect',ns)};positive=r['case'].startswith('positive');expected={'A':[1900 if positive else 1700,1000,500,500],'B':[2700,1000,500,500]}
 if hashlib.sha256(p.read_bytes()).hexdigest()!=r['saved_sha256'] or saved!=expected:errors.append('effect:'+r['id'])
 if r['input_mutations']!=int(positive) or r['bound_guard']!=positive or r['observer_exit']!=0:errors.append('admission:'+r['id'])
 observed={s['name']:s['position']+s['size'] for s in r['observer']['objects']}
 if observed!=saved or r['observer']['pid']==d['controller_pid']:errors.append('observer:'+r['id'])
 scores.append({'id':r['id'],'positive':positive,'bound_guard':r['bound_guard'],'saved':saved,'complete_or_correct_refusal':saved==expected})
if len(scores)!=6 or d['errors'] or d['parent_exit']!=0:errors.append('coverage_exit')
print(json.dumps({'scores':scores,'errors':errors,'decision':'SUPPORT_BOUND_REFERENCE_SCOPED' if not errors else 'FAIL_OR_HOLD','scope':'finite owned created-reference custody only, no atomic revision/general retention/modelvalue'},indent=2));raise SystemExit(bool(errors))
