"""Independent retained-file auditor. No candidate, reducer, or runner import.

Geometry is reconstructed with minidom/Decimal; raster evidence is decoded
with Pillow. This is independent implementation, not independent human review.
"""
import argparse,copy,hashlib,io,json,sys
from collections import Counter
from decimal import Decimal
from pathlib import Path
from xml.dom import minidom
from PIL import Image
ROOT=Path(__file__).resolve().parent
SCENARIOS=['MOVE_TARGET','MOVE_BOTH','DELETE_SENTINEL','RECOLOR_SENTINEL','DUPLICATE_SENTINEL','NO_EFFECT','MOVE_SENTINEL','PARTIAL_TARGET']
TAGS=['before_query','mutation','after_query','render']
def sha(b):return hashlib.sha256(b).hexdigest()
def same(a,b):return json.dumps(a,sort_keys=True)==json.dumps(b,sort_keys=True)
def num(x):
    v=Decimal(x)
    if not v.is_finite():raise ValueError('nonfinite')
    return v

def decode_svg(data):
    dom=minidom.parseString(data);root=dom.documentElement
    if root.localName!='svg' or root.namespaceURI!='http://www.w3.org/2000/svg':raise ValueError('root')
    if [num(root.getAttribute(k)) for k in ['width','height']]!=[320,180] or root.getAttribute('viewBox')!='0 0 320 180':raise ValueError('units')
    result={}
    for e in dom.getElementsByTagNameNS('http://www.w3.org/2000/svg','rect'):
        if e.parentNode is not root or e.hasAttribute('transform'):raise ValueError('unmodeled transform')
        name=e.getAttribute('id')
        if not name or name in result:raise ValueError('identity')
        color=e.getAttribute('fill')
        declarations=e.getAttribute('style').strip(';').split(';')
        for declaration in declarations:
            if declaration.strip():
                key,val=declaration.split(':',1)
                if key.strip()!='fill':raise ValueError('unmodeled style')
                color=val.strip()
        result[name]={'box':[num(e.getAttribute(k)) for k in ['x','y','width','height']],'fill':color}
    return result

def query_rows(raw):
    answer={}
    for s in raw.decode('utf-8').splitlines():
        fields=s.split(',')
        if len(fields)!=5 or fields[0] in answer:raise ValueError('query format')
        answer[fields[0]]=[num(v) for v in fields[1:]]
    return answer

def original_bytes(rep):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="320" height="180" viewBox="0 0 320 180">'
            f'<rect id="target" x="{20+rep*5}" y="{30+rep*3}" width="40" height="20" fill="#ff00aa"/>'
            f'<rect id="sentinel" x="{160+rep*5}" y="80" width="30" height="25" fill="#0080ff"/></svg>\n').encode()

def expected_action(s):
    target='select-by-id:target;transform-translate:30,0'
    return [target,'select-by-id:target,sentinel;transform-translate:30,0',
            target+';select-clear;select-by-id:sentinel;delete',
            target+';select-clear;select-by-id:sentinel;object-set-property:fill,#ff0000',
            target+';select-clear;select-by-id:sentinel;duplicate','select-clear',
            'select-by-id:sentinel;transform-translate:30,0','select-by-id:target;transform-translate:15,0'][SCENARIOS.index(s)]

def row_audit(row,blobs,index,rep,scenario):
    errors=[]
    def ck(b,n):
        if not b:errors.append(n)
    try:
        ck(type(row.get('index')) is int and row['index']==index,'index')
        ck(type(row.get('repetition')) is int and row['repetition']==rep,'repetition')
        ck(row.get('scenario')==scenario,'scenario')
        ck(row.get('authority') is False and type(row.get('model_calls')) is int and row['model_calls']==0 and type(row.get('native_input_events')) is int and row['native_input_events']==0,'no_authority')
        before_b=blobs['before.svg'];after_b=blobs['after.svg']
        ck(before_b==original_bytes(rep),'exact_input_fixture')
        before=decode_svg(before_b);after=decode_svg(after_b)
        ck(row['before_sha256']==sha(before_b) and row['after_sha256']==sha(after_b),'document_hashes')
        ck(same(row['contract'],{'before_sha256':sha(before_b),'target_id':'target','translation_x':30,'expected_ids':['sentinel','target']}),'authored_contract')
        ck(same(row['receipt'],{'exit':0,'document_sha256':sha(after_b)}),'effect_receipt')
        bq=query_rows(blobs['before_query.stdout']);aq=query_rows(blobs['after_query.stdout'])
        ck(all(bq.get(k)==v['box'] for k,v in before.items()),'before_query_xml')
        ck(all(aq.get(k)==v['box'] for k,v in after.items()),'after_query_xml')
        # Reconstruct the specific real-document interventions, not labels alone.
        expected=copy.deepcopy(before)
        if scenario in SCENARIOS[:5]:expected['target']['box'][0]+=30
        if scenario in ['MOVE_BOTH','MOVE_SENTINEL']:expected['sentinel']['box'][0]+=30
        if scenario=='DELETE_SENTINEL':del expected['sentinel']
        if scenario=='RECOLOR_SENTINEL':expected['sentinel']['fill']='#ff0000'
        if scenario=='PARTIAL_TARGET':expected['target']['box'][0]+=15
        if scenario=='DUPLICATE_SENTINEL':
            extra=set(after)-set(before);ck(len(extra)==1,'one_extra_object')
            if len(extra)==1:expected[next(iter(extra))]=copy.deepcopy(before['sentinel'])
        ck(after==expected,'real_application_effect')
        desired=list(before['target']['box']);desired[0]+=30
        primary='target' in after and after['target']['box']==desired
        protected=(after.keys()==before.keys() and after.get('target',{}).get('fill')==before['target']['fill'] and
                   all(after.get(k)==v for k,v in before.items() if k!='target'))
        full='COMPLETE_SUCCESS' if primary and protected else ('PARTIAL_REQUIRED_EFFECT_ONLY' if primary else 'FAILURE')
        old='PARTIAL_PRIMARY_RESTORED' if full=='PARTIAL_REQUIRED_EFFECT_ONLY' else full
        expected_views={
            'full':{'primary':primary,'preserved':protected,'legacy_outcome':old,'outcome':full,'required_only':'COMPLETE_SUCCESS' if primary else 'FAILURE','authority':False},
            'collateral_withheld':{'primary':primary,'preserved':None,'legacy_outcome':'UNKNOWN','outcome':'UNKNOWN','required_only':'COMPLETE_SUCCESS' if primary else 'FAILURE','authority':False},
            'wrong_document_digest':{'primary':None,'preserved':None,'legacy_outcome':'UNKNOWN','outcome':'UNKNOWN','required_only':'UNKNOWN','authority':False}}
        ck(same(row['results'],expected_views),'verifier_oracle')
        processes=row['processes'];ck(len(processes)==4,'process_count');last=-1
        for k,p in enumerate(processes):
            tag=TAGS[k];ck(p['tag']==tag,'process_role')
            ck(type(p['pid']) is int and p['pid']>0,'process_pid')
            ck(type(p['exit']) is int and p['exit']==0,'process_exit')
            ck(type(p['start_ns']) is int and type(p['end_ns']) is int and last<=p['start_ns']<=p['end_ns'],'process_time_order');last=p['end_ns']
            ck(p['stdout_sha256']==sha(blobs[tag+'.stdout']) and p['stderr_sha256']==sha(blobs[tag+'.stderr']),'process_wire_hash')
            ck(same(p,json.loads(blobs[tag+'.receipt.json'])),'process_receipt_copy')
            argv=p['argv'];ck(argv[0]=='/usr/bin/inkscape','application_binary')
            if tag=='mutation':ck('--actions='+expected_action(scenario) in argv,'action_binding')
            if tag.endswith('query'):ck(argv[-1]=='--query-all','read_only_query')
            ck(argv[1].endswith(f'/case-{index:03d}/'+('before.svg' if tag in ['before_query','mutation'] else 'after.svg')),'document_path')
            ck(p['document_sha256']==(None if tag=='before_query' else sha(after_b)),'query_bound_document')
        ck(type(row['verification_start_ns']) is int and last<=row['verification_start_ns']<=row['verification_end_ns'],'verification_clock')
        image=Image.open(io.BytesIO(blobs['after.png']));image.load();ck(image.size==(320,180),'render_dimensions');rgba=image.convert('RGBA')
        for v in after.values():
            x,y,w,h=v['box'];point=(int(x+w/2),int(y+h/2));color=v['fill']
            expected_color=tuple(int(color[j:j+2],16) for j in [1,3,5])+(255,)
            ck(rgba.getpixel(point)==expected_color,'raster_color')
        return errors,{'full':full,'primary':primary,'preserved':protected,'pixels_sha256':sha(rgba.tobytes()),'objects':len(after)}
    except Exception as e:
        errors.append('UNREADABLE:'+type(e).__name__+':'+str(e));return errors,{}

def load_batch(path):
    raw=json.loads((path/'RAW.json').read_bytes()); blobs=[]
    for row in raw['rows']:
        d=path/f"case-{row['index']:03d}"
        blobs.append({p.name:p.read_bytes() for p in d.iterdir() if p.is_file()})
    return raw,blobs

def inspect(out,construction=False,overrides=None):
    plan=json.loads((ROOT/'plan.json').read_text());errors=[];counts=Counter();facts=[]
    batch_count=1 if construction else 3
    for b in range(batch_count):
        d=out/f'batch-{b}';raw,blobs=load_batch(d)
        if overrides and b in overrides:raw,blobs=overrides[b]
        def ck(v,n):
            if not v:errors.append(f'batch-{b}:'+n)
        expected_freeze=None if construction else sha((ROOT/'FREEZE.json').read_bytes())
        ck(raw['allocation']==plan['allocation'] and raw['construction'] is construction,'allocation')
        ck(type(raw['batch']) is int and raw['batch']==b,'batch_identity')
        ck(raw['freeze_sha256']==expected_freeze,'freeze_binding')
        ck(raw['terminal']=='COMPLETE' and len(raw['rows'])==8,'denominator_terminal')
        external=json.loads((d/'EXTERNAL_EXIT.json').read_bytes());start=json.loads((d/'START.json').read_bytes())
        ck(type(external['exit']) is int and external['exit']==0 and external['timed_out'] is False,'external_exit')
        ck(external['runner_pid']==raw['runner_pid']==start['pid'] and type(raw['runner_pid']) is int,'runner_identity')
        if not overrides:
            ck(external['raw_sha256']==sha((d/'RAW.json').read_bytes()),'raw_byte_hash')
            ck(same([json.loads(x) for x in (d/'journal.jsonl').read_text().splitlines()],raw['rows']),'journal')
        ck(external['stdout_sha256']==sha((out/f'batch-{b}.stdout').read_bytes()) and external['stderr_sha256']==sha((out/f'batch-{b}.stderr').read_bytes()),'external_streams')
        pixel_map={}
        for k,row in enumerate(raw['rows']):
            if k>=8:errors.append('extra_row');break
            e,f=row_audit(row,blobs[k],b*8+k,b,SCENARIOS[k]);errors.extend(f'case-{b*8+k}:{s}' for s in e)
            if f:
                facts.append({'index':b*8+k,'scenario':SCENARIOS[k],**f});counts[f['full']]+=1;counts['required_only_complete']+=int(f['primary']);counts['legacy_false_complete']+=int(f['primary'] and f['full']!='COMPLETE_SUCCESS');counts['application_processes']+=len(row['processes']);pixel_map[SCENARIOS[k]]=f['pixels_sha256']
        ck(pixel_map.get('MOVE_TARGET')==pixel_map.get('DUPLICATE_SENTINEL') and 'MOVE_TARGET' in pixel_map,'same_pixels_different_document')
    return {'decision':'PASS_INKSCAPE_PRESERVED_DOCUMENT_SCOPED' if not errors else 'HOLD_AUDIT_OR_EVIDENCE','errors':errors,'cases':len(facts),'reporting_views':len(facts)*3,'counts':dict(counts),'rows':facts,'input_authority':False}

def corruption_controls(out,construction):
    original,original_blobs=load_batch(out/'batch-0');result={}
    mutations={
      'missing_row':lambda r,b:r['rows'].pop(),
      'duplicate_row':lambda r,b:r['rows'].__setitem__(1,copy.deepcopy(r['rows'][0])),
      'false_full_success':lambda r,b:r['rows'][1]['results']['full'].__setitem__('outcome','COMPLETE_SUCCESS'),
      'withheld_as_success':lambda r,b:r['rows'][0]['results']['collateral_withheld'].__setitem__('outcome','COMPLETE_SUCCESS'),
      'changed_required_contract':lambda r,b:r['rows'][0]['contract'].__setitem__('translation_x',31),
      'bool_repetition':lambda r,b:r['rows'][0].__setitem__('repetition',False),
      'bool_process_exit':lambda r,b:r['rows'][0]['processes'][0].__setitem__('exit',False),
      'bad_document_digest':lambda r,b:r['rows'][0].__setitem__('after_sha256','0'*64),
      'changed_query_bytes':lambda r,b:b[0].__setitem__('after_query.stdout',b[0]['after_query.stdout'].replace(b'target,50,',b'target,51,')),
      'changed_style':lambda r,b:b[3].__setitem__('after.svg',b[3]['after.svg'].replace(b'fill:#ff0000',b'fill:#0080ff')),
      'raster_missing':lambda r,b:b[0].__setitem__('after.png',b''),
      'authority_added':lambda r,b:r['rows'][0].__setitem__('authority',True),
      'lost_process':lambda r,b:r['rows'][0]['processes'].pop(),
      'source_freeze_changed':lambda r,b:r.__setitem__('freeze_sha256','0'*64)}
    for name,change in mutations.items():
        raw=copy.deepcopy(original);blobs=copy.deepcopy(original_blobs);change(raw,blobs)
        verdict=inspect(out,construction,{0:(raw,blobs)})
        result[name]={'rejected':bool(verdict['errors']),'errors':verdict['errors'][:4]}
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('out');ap.add_argument('--report',required=True);ap.add_argument('--construction',action='store_true');ap.add_argument('--controls',action='store_true');a=ap.parse_args();out=Path(a.out)
    source_errors=[]
    if not a.construction:
        frozen=json.loads((ROOT/'FREEZE.json').read_bytes())
        for p,h in frozen['source_sha256'].items():
            if sha((ROOT/p).read_bytes())!=h:source_errors.append(p)
    if source_errors:result={'decision':'STOP_SOURCE_MISMATCH','source_errors':source_errors,'rows_scored':0}
    else:
        try:result=inspect(out,a.construction)
        except Exception as e:result={'decision':'HOLD_AUDIT_OR_EVIDENCE','errors':[type(e).__name__+':'+str(e)]}
        result['source_errors']=[]
        if a.controls:
            result['corruption_controls']=corruption_controls(out,a.construction)
            if not all(x['rejected'] for x in result['corruption_controls'].values()):result['decision']='FAIL_AUDITOR_CONTROL'
    Path(a.report).write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result,sort_keys=True));return 0 if result['decision'].startswith('PASS') else 2
if __name__=='__main__':sys.exit(main())
