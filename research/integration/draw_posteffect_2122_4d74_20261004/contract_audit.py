import json,pathlib,hashlib,xml.etree.ElementTree as ET
O=pathlib.Path('/out');d=json.loads((O/'RAW.json').read_text());errors=[];scores=[];ns={'draw':'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0','svg':'urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0'}
for r in d['rows']:
 replacement=r['case'].startswith('replacement');p=O/(r['id']+'.fodg');rects=ET.parse(p).findall('.//draw:rect',ns);saved={s.get('{'+ns['draw']+'}name'):[round(float(s.get('{'+ns['svg']+'}'+k)[:-2])*1000) for k in ['x','y','width','height']] for s in rects};expected={'A':[1700 if replacement else 1900,1000,500,500],'B':[2700,1000,500,500]};observed={s['name']:s['position']+s['size'] for s in r['observer']['objects']};report='ABORT_EFFECT_UNCONFIRMED' if replacement else 'EFFECT_OBSERVED_AT_READ'
 if saved!=expected or observed!=saved or hashlib.sha256(p.read_bytes()).hexdigest()!=r['saved_sha256']:errors.append('effect:'+r['id'])
 if r['completion_report']!=report or r['recovery_mutations']!=0 or r['input_mutations']!=1 or r['post_membership_matches']!=int(not replacement) or r['post_effect_matches']!=bool(not replacement):errors.append('contract:'+r['id'])
 if replacement and not(r['guard_completed_ns']<r['late_writer_completed_ns']<r['setter_started_ns']):errors.append('ordering:'+r['id'])
 scores.append({'id':r['id'],'report':r['completion_report'],'post_membership_matches':r['post_membership_matches'],'saved':saved})
if len(scores)!=4 or d['errors'] or d['parent_exit']!=0:errors.append('coverage_exit')
print(json.dumps({'decision':'SUPPORT_POSTEFFECT_ABORT_SCOPED' if not errors else 'FAIL_OR_HOLD','errors':errors,'scores':scores,'scope':'post-effect detection only; replacement task and prevention remain failed'},indent=2));raise SystemExit(bool(errors))
