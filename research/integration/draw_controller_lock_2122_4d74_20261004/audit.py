import pathlib,json,hashlib,xml.etree.ElementTree as ET
O=pathlib.Path('/out');d=json.loads((O/'RAW.json').read_text());errors=[];scores=[];ns={'draw':'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0','svg':'urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0'}
for r in d['rows']:
 p=O/(r['id']+'.fodg');rects=ET.parse(p).findall('.//draw:rect',ns);saved={s.get('{'+ns['draw']+'}name'):[round(float(s.get('{'+ns['svg']+'}'+k)[:-2])*1000) for k in ['x','y','width','height']] for s in rects};replacement=r['case'].startswith('replacement');expected={'A':[1700 if replacement else 1900,1000,500,500],'B':[2700,1000,500,500]};titles={s.get('{'+ns['draw']+'}name'):s.findtext('svg:title',namespaces=ns) for s in rects}
 if hashlib.sha256(p.read_bytes()).hexdigest()!=r['saved_sha256'] or saved!=expected:errors.append('effect:'+r['id'])
 if r['input_mutations']!=int(not replacement):errors.append('admission:'+r['id'])
 if r['writer']['replacement_executed']!=replacement or replacement and r['writer']['new_reference_distinct'] is not True:errors.append('replacement_provenance:'+r['id'])
 observed={s['name']:s['position']+s['size'] for s in r['observer']['objects']}
 if observed!=saved or r['observer_exit']!=0:errors.append('observer:'+r['id'])
 generation='generation1' if replacement else 'generation0'
 if titles.get('A')!=generation or r['observer']['objects'][0]['generation']!=generation:errors.append('saved_generation:'+r['id'])
 scores.append({'id':r['id'],'replacement':replacement,'bound_guard':r['bound_guard'],'input_mutations':r['input_mutations'],'bound_state':r['bound_state'],'saved':saved,'generation':titles,'correct_effect_or_refusal':saved==expected and r['input_mutations']==int(not replacement)})
if len(scores)!=4 or d['errors'] or d['parent_exit']!=0:errors.append('coverage_exit')
print(json.dumps({'scores':scores,'errors':errors,'decision':'SUPPORT_REPLACEMENT_REFUSAL_SCOPED' if not errors else 'FAIL_OR_HOLD','scope':'actualreplacementboundary only; no oldB01regrade/universalidentity/modelvalue'},indent=2));raise SystemExit(bool(errors))
