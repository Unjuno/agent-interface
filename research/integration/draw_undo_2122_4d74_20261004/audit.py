import pathlib,json,hashlib,xml.etree.ElementTree as ET
r=pathlib.Path('/study');out=pathlib.Path('/out');raw=json.loads((out/'raw.json').read_text(encoding='utf-8-sig'));errors=[];scores=[]
ns={'draw':'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0','svg':'urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0'}
for row in raw['rows']:
    case=row['case'];path=out/(case+'.fodg')
    if not path.exists():errors.append('missing_saved:'+case);continue
    if hashlib.sha256(path.read_bytes()).hexdigest()!=row['saved_sha256']:errors.append('saved_hash:'+case)
    tree=ET.parse(path);rects=tree.findall('.//draw:rect',ns)
    saved=[{k:s.get('{'+ns['svg']+'}'+k) for k in ['x','y','width','height']} for s in rects]
    events=row['events'];before=events[0];changed=events[1];last=events[-1]
    if not row['mutation_observed'] or before['objects']==changed['objects']:errors.append('no_mutation:'+case)
    recorded=changed['undo_possible'] and bool(changed['titles'])
    if recorded:
        if last['stage']!='after_undo' or last['objects']!=before['objects'] or row['disposition']!='RECORDING_QUALIFIED_SCOPED':errors.append('restoration:'+case)
    elif row['disposition']!='HOLD_OPERATION_NOT_RECORDED' or last['stage']!='after_operation':errors.append('unrecorded_classification:'+case)
    objects=last['objects']
    if len(saved)!=len(objects):errors.append('saved_count:'+case)
    for s,obj in zip(saved,objects):
        def units(v):
            if v.endswith('cm'):return round(float(v[:-2])*1000)
            if v.endswith('mm'):return round(float(v[:-2])*100)
            raise ValueError('unqualified_unit:'+v)
        actual=[units(s[k]) for k in ['x','y','width','height']]
        if actual!=obj['position']+obj['size']:errors.append('saved_geometry:'+case)
    scores.append({'case':case,'recorded':recorded,'disposition':row['disposition'],'saved_rectangles':saved})
if raw['errors'] or raw['parent_exit']!=0:errors.append('producer_cleanup')
if len(scores)!=2:errors.append('case_coverage')
print(json.dumps({'scores':scores,'errors':errors,'decision':'ELIGIBILITY_AUDITED_SCOPED' if not errors else 'FAIL_OR_HOLD','scope':'independent saved XML geometry and raw classification; no task/model/semantic ownership proof'},indent=2));raise SystemExit(bool(errors))
