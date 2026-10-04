import json,pathlib,hashlib,xml.etree.ElementTree as ET
O=pathlib.Path('/out');d=json.loads((O/'RAW.json').read_text());errors=[];ns={'draw':'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0','svg':'urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0'};goal=[['A',1900,1000],['B',2700,1000]]
for r in d['rows']:
 mutated=r['id']=='mutated';expected=[['A',1800 if mutated else 1900,1000],['B',2700 if mutated else 2800,1000]];p=O/(r['id']+'.fodg');saved=[[x.get('{'+ns['draw']+'}name')]+[round(float(x.get('{'+ns['svg']+'}'+k)[:-2])*1000) for k in ['x','y']] for x in ET.parse(p).findall('.//draw:rect',ns)];observed=[[x['name']]+x['position'] for x in r['observer']['objects']]
 if saved!=expected or observed!=saved or r['after']!=saved or hashlib.sha256(p.read_bytes()).hexdigest()!=r['saved_sha256']:errors.append('effect:'+r['id'])
 if r['split_satisfied']!=mutated or r['fresh_satisfied'] or r['controller_mutations_after_setup']!=0:errors.append('read_contract:'+r['id'])
 if mutated:
  if r['writer']['prefixes']!=[[['A',1800,1000],['B',2800,1000]],expected] or goal in [r['before']]+r['writer']['prefixes']:errors.append('prefix_truth')
  if not(r['read_A_completed_ns']<r['writer_completed_ns']<r['read_B_completed_ns']):errors.append('ordering')
if [r['id'] for r in d['rows']]!=['stable','mutated'] or d['errors'] or d['parent_exit']!=0:errors.append('coverage_exit')
print(json.dumps({'decision':'SUPPORT_FRACTURED_DRAW_READ_SCOPED' if not errors else 'FAIL_OR_HOLD','errors':errors,'scope':'actual serialized writer prefixes; no atomic snapshot remedy or natural race-rate claim'},indent=2));raise SystemExit(bool(errors))
