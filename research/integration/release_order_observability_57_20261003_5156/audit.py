"""Independent raw-only reconstruction. Never imports producer or kernel."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys

HERE=Path(__file__).resolve().parent
def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)
def sha(data):return hashlib.sha256(data).hexdigest()
def equal_json(a,b):return canonical(a)==canonical(b)
def reduce_events(events):
    if type(events) is not list or len(events)!=4:raise ValueError('exact four events required')
    kinds=[];last_ns=-1;key_up=True;snapshot=None;press_seq=None;release_seq=None
    for position,event in enumerate(events,1):
        if type(event) is not dict:raise ValueError('event must be object')
        expected_keys={'seq','kind','ns'} | ({'key'} if event.get('kind') in ('press','release') else set())
        if set(event)!=expected_keys:raise ValueError('event exact keys')
        if type(event['seq']) is not int or event['seq']!=position:raise ValueError('event sequence')
        if type(event['ns']) is not int or event['ns']<last_ns:raise ValueError('event monotonic exact integer clock')
        last_ns=event['ns'];kind=event['kind'];kinds.append(kind)
        if kind in ('press','release') and event['key']!='A':raise ValueError('one key domain')
        if kind=='press':key_up=False;press_seq=position
        elif kind=='release':key_up=True;snapshot=[];release_seq=position
        elif kind not in ('start','end'):raise ValueError('unknown event')
    if sorted(kinds)!=['end','press','release','start'] or kinds[0]!='start':raise ValueError('event census')
    return {'terminal_keys_down':[] if key_up else ['A'],
        'release_snapshot_keys_down':snapshot,'ordered':press_seq<release_seq}

def expected_projection(case):
    return {'command_id':'modeled-one-press',
        'backend_receipt_id':'model-release-'+str(case['ended_ns'])+'-'+str(case['release_ns']),
        'invariant_manifest_id':'2'*64,'lease_id':'model-lease','observation_sequence':1,
        'surface_id':'model-surface','started_ns':100,'ended_ns':case['ended_ns'],
        'action_count':1,'effect_occurrence':'observed',
        'release':{'observed_ns':case['release_ns'],'verified':True,'keys_down':[],'buttons_down':[]}}

def expected_ids():
    ids=set()
    for end in (700,900):
        for press in (200,400,600):
            for release in (200,400,600,end,end+100):
                for order in (('press-release','release-press') if press==release else ('time',)):
                    ids.add(f'e{end}-p{press}-r{release}-{order}')
    return ids

def validate_case(case):
    if type(case) is not dict or set(case)!={'case_id','ended_ns','press_ns','release_ns','tie_order','events'}:
        raise ValueError('case exact keys')
    m=re.fullmatch(r'e(700|900)-p(200|400|600)-r([0-9]+)-(time|press-release|release-press)',case['case_id'])
    if m is None:raise ValueError('case ID syntax')
    end,press,release=map(int,m.groups()[:3]);order=m.group(4)
    for name,value in [('ended_ns',end),('press_ns',press),('release_ns',release)]:
        if type(case[name]) is not int or case[name]!=value:raise ValueError('case vector '+name)
    if release not in (200,400,600,end,end+100) or case['tie_order']!=order:raise ValueError('case vector domain')
    if (press==release)==(order=='time'):raise ValueError('case tie domain')
    reduced=reduce_events(case['events'])
    events={e['kind']:e for e in case['events']}
    for kind,value in [('start',100),('end',end),('press',press),('release',release)]:
        if events[kind]['ns']!=value:raise ValueError('case event clock '+kind)
    if press==release and reduced['ordered']!=(order=='press-release'):raise ValueError('case tied order')

def verify(raw):
    errors=[];groups={};kernel_wrong=0;end_wrong=0;ordered_wrong=0
    try:
        cases_document=json.loads((HERE/'cases.json').read_text(encoding='utf8'))
        cases=cases_document['cases'];by_id={c['case_id']:c for c in cases}
        if len(cases)!=36 or set(by_id)!=expected_ids():errors.append('frozen case census')
        for case in cases:validate_case(case)
        freeze_bytes=(HERE/'FREEZE.json').read_bytes()
        for name,expected in json.loads(freeze_bytes)['sha256'].items():
            if sha((HERE/name).read_bytes())!=expected:errors.append('frozen input '+name)
        if type(raw) is not dict or set(raw)!={'schema','freeze_sha256','cases_sha256','source_identity','rows'}:
            raise ValueError('raw exact keys')
        if raw['schema']!='kernel-release-order-raw-v1':errors.append('raw schema')
        if raw['freeze_sha256']!=sha(freeze_bytes):errors.append('freeze hash')
        if raw['cases_sha256']!=sha((HERE/'cases.json').read_bytes()):errors.append('cases hash')
        if not equal_json(raw['source_identity'],json.loads((HERE/'SOURCE.json').read_text(encoding='utf8'))):errors.append('source identity')
        rows=raw['rows']
        if type(rows) is not list or len(rows)!=36:raise ValueError('raw row count')
        if [r.get('case_id') for r in rows]!=[c['case_id'] for c in cases]:errors.append('exact row order and census')
        for row in rows:
            if type(row) is not dict or set(row)!={'case_id','case_sha256','events','release_snapshot_keys_down','terminal_keys_down','projection','kernel_outcome','comparators'}:
                raise ValueError('row exact keys')
            case=by_id[row['case_id']]
            if row['case_sha256']!=sha(canonical(case).encode()):errors.append('case hash '+row['case_id'])
            if not equal_json(row['events'],case['events']):errors.append('case events '+row['case_id'])
            reduced=reduce_events(row['events'])
            if not equal_json(row['release_snapshot_keys_down'],reduced['release_snapshot_keys_down']):errors.append('snapshot state')
            if not equal_json(row['terminal_keys_down'],reduced['terminal_keys_down']):errors.append('terminal state')
            projection=expected_projection(case)
            if not equal_json(row['projection'],projection):errors.append('typed full projection')
            expected_outcome={'stage':'unavailable','reason':'unavailable','command_id':'modeled-one-press',
                'effect_occurred':True,'effect_verified':False,'release_verified':True}
            if not equal_json(row['kernel_outcome'],expected_outcome):errors.append('actual kernel outcome')
            comparators={'end_floor':case['release_ns']>=case['ended_ns'],'ordered_witness':reduced['ordered']}
            if not equal_json(row['comparators'],comparators):errors.append('comparator reconstruction')
            truth=reduced['terminal_keys_down']==[]
            kernel_wrong+=row['kernel_outcome']['release_verified'] is not truth
            end_wrong+=row['comparators']['end_floor'] is not truth
            ordered_wrong+=row['comparators']['ordered_witness'] is not truth
            groups.setdefault(canonical(projection),[]).append({'case_id':row['case_id'],'terminal_empty':truth})
        mixed=[values for values in groups.values() if len({x['terminal_empty'] for x in values})==2]
        if len(mixed)!=6 or kernel_wrong!=12 or end_wrong!=12 or ordered_wrong!=0:
            errors.append('prospective predictions disagree; retain HOLD')
        return {'integrity':'PASS' if not errors else 'HOLD','errors':errors,'rows':len(rows),
            'model_decision':'FAIL_TERMINAL_RELEASE_IDENTIFIABILITY' if mixed and not errors else 'HOLD',
            'mixed_full_projection_classes':mixed,'kernel_false_release_reports':kernel_wrong,
            'end_floor_wrong_refusals':end_wrong,'ordered_witness_disagreements':ordered_wrong}
    except (AttributeError,KeyError,TypeError,ValueError,OSError) as e:
        return {'integrity':'HOLD','model_decision':'HOLD','errors':errors+[type(e).__name__+': '+str(e)]}

def corruptions(raw):
    variants=[]
    def add(name,change):
        v=deepcopy(raw);change(v);variants.append((name,v))
    add('boolean-action-count',lambda v:v['rows'][0]['projection'].__setitem__('action_count',True))
    add('floating-end',lambda v:v['rows'][0]['projection'].__setitem__('ended_ns',700.0))
    add('flip-kernel-release',lambda v:v['rows'][0]['kernel_outcome'].__setitem__('release_verified',False))
    add('flip-end-floor',lambda v:v['rows'][0]['comparators'].__setitem__('end_floor',not v['rows'][0]['comparators']['end_floor']))
    add('flip-ordered-witness',lambda v:v['rows'][0]['comparators'].__setitem__('ordered_witness',not v['rows'][0]['comparators']['ordered_witness']))
    add('snapshot-nonempty',lambda v:v['rows'][0].__setitem__('release_snapshot_keys_down',['A']))
    add('terminal-state-flip',lambda v:v['rows'][0].__setitem__('terminal_keys_down',['A']))
    add('drop-event',lambda v:v['rows'][0]['events'].pop())
    add('boolean-sequence',lambda v:v['rows'][0]['events'][0].__setitem__('seq',True))
    add('duplicate-row',lambda v:v['rows'].__setitem__(1,deepcopy(v['rows'][0])))
    add('wrong-freeze',lambda v:v.__setitem__('freeze_sha256','0'*64))
    add('extra-projection-field',lambda v:v['rows'][0]['projection'].__setitem__('press_ns',200))
    return variants

def main():
    raw_path=Path(sys.argv[1]);output=Path(sys.argv[2])
    if output.exists():raise FileExistsError('audit output already exists')
    raw=json.loads(raw_path.read_text(encoding='utf8'));report=verify(raw)
    controls=[]
    for name,changed in corruptions(raw):
        assert not equal_json(raw,changed),name
        finding=verify(changed)
        controls.append({'name':name,'refused':finding['integrity']=='HOLD','errors':finding['errors']})
    report['corruption_controls']=controls;report['raw_sha256']=sha(raw_path.read_bytes())
    if not all(c['refused'] for c in controls):report['integrity']='HOLD';report['errors'].append('ineffective corruption control')
    output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf8')
    print(json.dumps({'integrity':report['integrity'],'model_decision':report['model_decision'],'rows':report.get('rows'),'corruptions_refused':sum(c['refused'] for c in controls)}))
    return 0 if report['integrity']=='PASS' else 1

if __name__=='__main__':sys.exit(main())
