import pathlib,json,hashlib,xml.etree.ElementTree as ET
O=pathlib.Path('/out');raw=json.loads((O/'RAW.json').read_text());errors=[];scores=[];groups={'temporary':{'n':0,'failed':0},'held':{'n':0,'failed':0}}
ns={'draw':'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0','svg':'urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0'}
def units(v):return round(float(v[:-2])*(1000 if v.endswith('cm') else 100))
for row in raw['rows']:
 name=row['id'];p=O/(name+'.fodg');events={e['stage']:e for e in row['events']};saved={s.get('{'+ns['draw']+'}name'):[units(s.get('{'+ns['svg']+'}'+k)) for k in ['x','y','width','height']] for s in ET.parse(p).findall('.//draw:rect',ns)};expected={'A':[1900,1000,500,500],'B':[2700,1000,500,500]}
 if hashlib.sha256(p.read_bytes()).hexdigest()!=row['saved_sha256']:errors.append('hash:'+name)
 if row['setter_argument']!=[1900,1000] or row['setter_name']!='A' or row['setter_type']!='com.sun.star.drawing.RectangleShape' or row['observer_exit']!=0:errors.append('setter_or_observer:'+name)
 observer={s['name']:s['position']+s['size'] for s in row['observer']['objects']}
 if observer!=saved or row['observer']['pid']==raw['controller_pid'] or not row['observer']['locked']:errors.append('independent_join:'+name)
 complete=saved==expected;g=groups['held' if row['hold_reference'] else 'temporary'];g['n']+=1;g['failed']+=not complete
 if saved.get('B')!=expected['B']:errors.append('protected_B:'+name)
 scores.append({'id':name,'held':row['hold_reference'],'setter_proxy_position':row['setter_proxy_position'],'immediate_A':events['final']['objects'][0]['position'],'observer':observer,'saved':saved,'complete':complete})
if len(scores)!=8 or raw['errors'] or raw['parent_exit']!=0:errors.append('coverage_exit')
decision='HOLD_NOT_EXPOSED' if groups['temporary']['failed']==0 else 'SUPPORT_RETENTION_DISCRIMINATOR_SCOPED' if groups['held']['failed']==0 else 'HOLD_RETENTION_NOT_SUFFICIENT'
if errors:decision='FAIL_OR_HOLD'
print(json.dumps({'scores':scores,'groups':groups,'errors':errors,'decision':decision,'scope':'proxyretentiononly, no internalpointerrootcause/modelvalue/sourceadoption'},indent=2));raise SystemExit(bool(errors))
