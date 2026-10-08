import pathlib,json,hashlib,xml.etree.ElementTree as ET
O=pathlib.Path('/out');raw=json.loads((O/'RAW.json').read_text());errors=[];scores=[];groups={'0':{'n':0,'immediate_fail':0,'saved_fail':0},'9':{'n':0,'immediate_fail':0,'saved_fail':0}}
ns={'draw':'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0','svg':'urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0'}
def units(v):return round(float(v[:-2])*(1000 if v.endswith('cm') else 100))
for row in raw['rows']:
 name=row['id'];p=O/(name+'.fodg');events={e['stage']:e for e in row['events']};saved={s.get('{'+ns['draw']+'}name'):[units(s.get('{'+ns['svg']+'}'+k)) for k in ['x','y','width','height']] for s in ET.parse(p).findall('.//draw:rect',ns)}
 if hashlib.sha256(p.read_bytes()).hexdigest()!=row['saved_sha256']:errors.append('saved_hash:'+name)
 if row['setter_argument']!=[1900,1000] or not row['current_guard_matches'] or row['writer_exit']!=0:errors.append('setter_or_writer:'+name)
 if row['writer']['after']!=[['A',1700,1000],['B',2700,1000]]:errors.append('writer_values:'+name)
 immediate=events['final']['objects'][0]['position']==[1900,1000];expected={'A':[1900,1000,500,500],'B':[2700,1000,500,500]};complete=saved==expected;g=groups[str(row['requested_wait_seconds'])];g['n']+=1;g['immediate_fail']+=not immediate;g['saved_fail']+=not complete
 if saved.get('B')!=expected['B']:errors.append('protected_B:'+name)
 scores.append({'id':name,'wait_ns':row['actual_wait_ns'],'setter_argument':row['setter_argument'],'immediate_A':events['final']['objects'][0]['position'],'100ms_A':events['after_100ms']['objects'][0]['position'],'1s_A':events['after_1s']['objects'][0]['position'],'saved':saved,'immediate_complete':immediate,'saved_complete':complete})
if len(scores)!=8 or raw['errors'] or raw['parent_exit']!=0:errors.append('coverage_or_exit')
decision='HOLD_NOT_REPRODUCED' if groups['0']['immediate_fail']==0 else 'SUPPORT_WAIT_DISCRIMINATOR_SCOPED' if groups['9']['immediate_fail']==0 else 'HOLD_WAIT_NOT_SUFFICIENT'
if errors:decision='FAIL_OR_HOLD'
print(json.dumps({'scores':scores,'groups':groups,'errors':errors,'decision':decision,'scope':'new diagnosticonly; no internalrootcause/operationaldelay/modelbenefit/oldrunregrade'},indent=2));raise SystemExit(bool(errors))
