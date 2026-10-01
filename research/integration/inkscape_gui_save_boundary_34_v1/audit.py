"""Raw-only independent audit. No GUI, input, candidate, Pillow or Inkscape imports."""
from __future__ import annotations
import argparse,copy,hashlib,json,re,zlib
from fractions import Fraction
from pathlib import Path
import xml.etree.ElementTree as ET

EXPECTED={
 'NO_TASK_ACTION':(0,40,[]),
 'MOVE_NO_SAVE':(20,40,['task_move']),
 'MOVE_SAVE':(20,60,['task_move','task_save']),
 'SAVE_THEN_UNSAVED_MOVE':(40,60,['task_move','task_save','task_move']),
 'MOVE_UNDO_SAVE':(0,40,['task_move','task_undo','task_save']),
 'SAVE_THEN_UNSAVED_UNDO':(0,60,['task_move','task_save','task_undo'])}
SVG_NS='{http://www.w3.org/2000/svg}'
def digest(b):return hashlib.sha256(b).hexdigest()
def shape(b):
    root=ET.fromstring(b)
    if root.tag!=SVG_NS+'svg' or root.attrib.get('viewBox')!='0 0 320 180':raise ValueError('SVG_ROOT')
    found={}
    for el in root:
        if el.tag==SVG_NS+'rect':
            key=el.attrib['id']
            if key in found:raise ValueError('DUPLICATE_RECT')
            if set(el.attrib)!=set(['id','x','y','width','height','fill']):raise ValueError('RECT_SCHEMA')
            found[key]=[Fraction(el.attrib[k]) for k in ['x','y','width','height']]+[el.attrib['fill']]
        elif el.tag in [SVG_NS+'defs','{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}namedview']:pass
        else:raise ValueError('UNEXPECTED_NODE')
    if set(found)!=set(['target','sentinel']):raise ValueError('OBJECT_INVENTORY')
    return found

def raster_bounds(raw,color):
    if len(raw)!=1024*768*3:raise ValueError('RGB_SIZE')
    # Independent search by byte pattern, with explicit RGB alignment and ROI.
    needle=bytes(color);i=-1;xs=[];ys=[]
    while True:
        i=raw.find(needle,i+1)
        if i<0:break
        if i%3:continue
        k=i//3;y,x=divmod(k,1024)
        if 150<=y<658 and 70<=x<700:xs.append(x);ys.append(y)
    if not xs:raise ValueError('COLOR_ABSENT')
    return [min(xs),min(ys),max(xs)+1,max(ys)+1,len(xs)]

def neutral(n):
    return type(n) is dict and type(n.get('keys')) is list and len(n['keys'])==32 and all(type(v) is int and v==0 for v in n['keys']) and type(n.get('button_mask')) is int and n['button_mask']==0

def inspect_case(path:Path,override=None, byte_overrides=None):
    r=json.loads((path/'case.json').read_bytes()) if override is None else override
    byte_overrides={} if byte_overrides is None else byte_overrides
    def read(name):return byte_overrides.get(name,(path/name).read_bytes())
    errors=[]
    def ck(v,name):
        if not v:errors.append(name)
    try:
        ck(r['status']=='COMPLETE','status');ck(type(r['repetition']) is int,'repetition_type')
        ck(r['public_runtime'] is False and r['model_calls']==0 and r['authority_scope']=='private_fixture_only','scope')
        ck(neutral(r['initial_neutral']) and neutral(r['pre_cleanup_neutral']),'neutrality')
        ck(r['socket_absent'] is True and 'release_error' not in r,'cleanup')
        ck(r['pixel_format']['depth']==24 and r['pixel_format']['image_byte_order']==0,'pixel_format')
        ps=r['processes'];ck([p['name'] for p in ps]==['xvfb','openbox','inkscape'],'process_roles')
        ck(all(type(p['pid']) is int and p['pid']>0 and type(p['returncode']) is int and not p.get('forced_kill') and p['end_ns']>=p['teardown_request_ns']>=p['start_ns'] for p in ps),'process_exits')
        ck([p['returncode'] for p in ps]==[0,0,-15],'expected_teardown')
        ck(ps[-1]['pid'] in r['target_window']['pid'],'app_window_pid')
        ck(len(r['queries'])==2 and all(type(q['returncode']) is int and q['returncode']==0 and q['end_ns']>=q['start_ns'] for q in r['queries']),'query_exits')
        obs=r['observations'];ck(set(obs)=={'ready','before','final'},'snapshot_denominator')
        bb={}
        for lab in ['ready','before','final']:
            rgb=zlib.decompress(read(lab+'.rgb.z'));doc=read(lab+'.svg');o=obs[lab]
            ck(digest(rgb)==o['rgb_sha256'],'rgb_digest_'+lab);ck(digest(doc)==o['document_sha256'],'document_digest_'+lab)
            ck(type(o['capture_start_ns']) is int and o['capture_start_ns']<=o['capture_end_ns']<=o['document_read_start_ns']<=o['document_read_end_ns'],'capture_order_'+lab)
            ck(neutral(o['neutral']),'snapshot_neutral_'+lab)
            bb[lab]={k:raster_bounds(rgb,c) for k,c in [('target',(255,0,170)),('sentinel',(0,128,255))]}
            ck(bb[lab]==o['boxes'],'measured_box_'+lab)
        a,b=bb['before'],bb['final'];shift=b['target'][0]-a['target'][0]
        ck(a['target'][2]-a['target'][0]==49 and a['target'][3]-a['target'][1]==39,'selected_geometry')
        ck(b['target']==[a['target'][0]+shift,a['target'][1],a['target'][2]+shift,a['target'][3],a['target'][4]],'rigid_translation')
        ck(a['sentinel']==b['sentinel'],'canvas_collateral')
        before,after=shape(read('before.svg')),shape(read('final.svg'))
        ck(before=={'target':[40,60,50,40,'#ff00aa'],'sentinel':[200,100,50,30,'#0080ff']},'initial_document')
        for lab,d in [('before',before),('final',after)]:
            rows={}
            for line in read(lab+'.query').decode().splitlines():
                vals=line.split(',');ck(len(vals)==5,'query_row_shape')
                if len(vals)==5:
                    ck(vals[0] not in rows,'query_duplicate');rows[vals[0]]=[Fraction(v) for v in vals[1:]]
            ck(all(rows.get(key)==v[:4] for key,v in d.items()),'independent_query_'+lab)
        primary=after['target'][:4]==[60,60,50,40]
        preserved=after['sentinel']==before['sentinel'] and after['target'][4]==before['target'][4]
        ck(preserved,'saved_collateral')
        contract=r['saved_contract'];ck(contract=={'before_sha256':digest(read('before.svg')),'target_id':'target','translation_x':20,'expected_ids':['sentinel','target']},'contract')
        ck(type(r['saved_receipt']['exit']) is int and r['saved_receipt']=={'exit':0,'document_sha256':digest(read('final.svg'))},'receipt')
        saved=r['result']['saved'];outcome='COMPLETE_SUCCESS' if primary else 'FAILURE'
        ck(saved=={'primary':primary,'preserved':True,'legacy_outcome':outcome,'outcome':outcome,'required_only':outcome,'authority':False},'candidate_saved')
        ck(r['result']['canvas_required'] is (shift==20) and r['result']['canvas_sentinel_preserved'] is True and r['result']['authority'] is False and r['result']['replay_authorized'] is False,'candidate_canvas')
        move,disk_x,actions=EXPECTED[r['scenario']]
        ck(shift==move and after['target']==[disk_x,60,50,40,'#ff00aa'],'planned_contrast')
        task=[ev for ev in r['input'] if ev['role'].startswith('task_')]
        ck([ev['role'] for ev in task]==actions,'task_sequence')
        expected_keys={'task_move':['Shift_L','Right'],'task_save':['Control_L','s'],'task_undo':['Control_L','z']}
        for ev in r['input']:
            ck(neutral(ev['before']) and neutral(ev['after']),'input_release')
            ck(type(ev['start_ns']) is int and ev['start_ns']<=ev['end_ns'],'input_time')
            ck(ev['focus']==ev['focus_ancestry'][0] and r['target_window']['id'] in ev['focus_ancestry'],'input_focus')
            if ev['role'] in expected_keys:ck(ev['names']==expected_keys[ev['role']],'key_mapping')
        return {'errors':errors,'scenario':r['scenario'],'rep':r['repetition'],'screen_dx':shift,'saved_x':int(after['target'][0]),'canvas_required':shift==20,'saved_required':primary,'neutral':not any(x.startswith('input_release') for x in errors),'task_chords':len(task)}
    except Exception as e:
        return {'errors':errors+['UNREADABLE:'+type(e).__name__+':'+str(e)],'scenario':r.get('scenario')}

def audit(root:Path, controls=False):
    freeze=json.loads((root/'FREEZE.json').read_text());errors=[]
    for n,h in freeze['sources'].items():
        if digest((root/n).read_bytes())!=h:errors.append('source:'+n)
    if errors:return {'decision':'STOP_SOURCE_MISMATCH','errors':errors}
    plan=json.loads((root/'plan.json').read_text());rows=[]
    for batch in range(4):
        bp=root/'formal'/f'batch-{batch}'
        try:
            ex=json.loads((bp/'external.json').read_text());er=json.loads((bp/'end.json').read_text())
            if type(ex['returncode']) is not int or ex['returncode']!=0:errors.append('batch_exit:'+str(batch))
            if er['indices']!=list(range(batch*3,batch*3+3)) or er['freeze_sha256']!=digest((root/'FREEZE.json').read_bytes()):errors.append('batch_binding:'+str(batch))
            for i in range(batch*3,batch*3+3):
                p=bp/f'case-{i:02d}';r=inspect_case(p);rows.append(r)
                if r['errors']:errors.extend([f'case-{i}:'+a for a in r['errors']])
                sr=json.loads((p/'supervisor.json').read_text());raw=(p/'case.json').read_bytes()
                if type(sr['returncode']) is not int or sr['returncode']!=0 or sr['case_sha256']!=digest(raw):errors.append('case_external:'+str(i))
                if [r.get('scenario'),r.get('rep')]!=plan['cases'][i]:errors.append('case_schedule:'+str(i))
        except Exception as e:errors.append('batch_unavailable:'+str(batch)+':'+str(e))
    result={'decision':'PASS_GUI_CANVAS_SAVE_BOUNDARY_SCOPED' if not errors and len(rows)==12 else 'HOLD_GUI_SAVE_EVIDENCE_OR_GATE','errors':errors,'rows':rows,'cases':len(rows),'source_freeze_sha256':digest((root/'FREEZE.json').read_bytes()),'public_runtime':False,'model_calls':0}
    if controls and not errors:
        p=root/'formal/batch-0/case-00';original=json.loads((p/'case.json').read_text());mutations={}
        def test(name,fn):
            m=copy.deepcopy(original);fn(m);o=inspect_case(p,m);mutations[name]={'rejected':bool(o['errors']),'errors':o['errors']}
        test('bool_repetition',lambda m:m.update(repetition=True))
        test('missing_process',lambda m:m['processes'].pop())
        test('bool_exit',lambda m:m['processes'][0].update(returncode=False))
        test('false_saved_complete',lambda m:m['result']['saved'].update(outcome='COMPLETE_SUCCESS'))
        test('false_canvas',lambda m:m['result'].update(canvas_required=True))
        test('wrong_digest',lambda m:m['observations']['final'].update(document_sha256='0'*64))
        test('wrong_box',lambda m:m['observations']['final']['boxes']['target'].__setitem__(0,999))
        test('nonneutral_key',lambda m:m['pre_cleanup_neutral']['keys'].__setitem__(0,1))
        test('extra_task',lambda m:m['input'].append(dict(m['input'][-1],role='task_save',names=['Control_L','s'])))
        test('query_nonzero',lambda m:m['queries'][0].update(returncode=2))
        test('authority_added',lambda m:m['result'].update(authority=True))
        test('wrong_document_scope',lambda m:m['saved_contract'].update(target_id='sentinel'))
        test('future_capture',lambda m:m['observations']['final'].update(capture_start_ns=10**30))
        result['corruption_controls']=mutations
        if not all(v['rejected'] for v in mutations.values()):result['decision']='FAIL_AUDIT_CONTROL'
    return result
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--controls',action='store_true');a=ap.parse_args()
    r=audit(a.root.resolve(),a.controls)
    with a.output.open('x') as f:json.dump(r,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps({'decision':r['decision'],'cases':r.get('cases'),'errors':r['errors']}));raise SystemExit(0 if r['decision'].startswith('PASS') else 2)
